import json
from datetime import date
from flask import request, jsonify
from app import db
from models import User, AiDietPlan, AiPlanRun, AiReport
from services.ai_service import generate_weekly_report, format_taboo_prompt
from services.errors import DomainError
from services.health_check import load_user_diseases
from services.planning.pipeline import generate_trusted_plan
from services import stats_service
from utils.auth import auth_required, ensure_owner, resolve_user_id
from . import api


def _meal_ids(selection, meal):
    return ','.join(str(dish.recipe_id) for dish in getattr(selection, meal))


@api.route('/ai/plan', methods=['POST'])
@auth_required
def create_ai_plan():
    data = request.get_json() or {}
    user_id, err = resolve_user_id(data.get('user_id'))
    if err:
        return err

    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'msg': '用户不存在'}), 404

    diseases = load_user_diseases(user.user_id)

    try:
        result = generate_trusted_plan(user, diseases)
    except DomainError:
        raise
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'AI方案生成失败: {str(e)}'}), 500

    if not result.plan or not result.verification.total_cal:
        return jsonify({'code': 500, 'msg': 'AI方案未生成有效内容，请稍后重试'}), 500

    plan = AiDietPlan(
        user_id=user.user_id,
        create_date=date.today(),
        plan_content=json.dumps(result.plan, ensure_ascii=False),
        breakfast_ids=_meal_ids(result.selection, 'breakfast'),
        lunch_ids=_meal_ids(result.selection, 'lunch'),
        dinner_ids=_meal_ids(result.selection, 'dinner'),
        snack_ids=_meal_ids(result.selection, 'snack'),
        forbid_food=format_taboo_prompt(diseases) if diseases else None,
        total_cal=round(result.verification.total_cal),
    )
    db.session.add(plan)
    db.session.flush()

    run = AiPlanRun(user_id=user.user_id, plan_id=plan.plan_id, **result.metrics)
    db.session.add(run)
    db.session.commit()
    db.session.refresh(plan)

    data = plan.to_dict()
    data['verification'] = result.plan.get('verification')
    data['warnings'] = result.warnings
    return jsonify({'code': 200, 'msg': '方案生成成功', 'data': data}), 200


@api.route('/ai/plan', methods=['GET'])
@auth_required
def list_ai_plans():
    user_id, err = resolve_user_id(request.args.get('user_id', type=int))
    if err:
        return err

    limit = request.args.get('limit', 5, type=int)
    plans = AiDietPlan.query.filter_by(user_id=user_id) \
        .order_by(AiDietPlan.create_date.desc()) \
        .limit(limit).all()
    return jsonify({'code': 200, 'data': [p.to_dict() for p in plans]})


@api.route('/ai/report', methods=['POST'])
@auth_required
def create_ai_report():
    data = request.get_json() or {}
    user_id, err = resolve_user_id(data.get('user_id'))
    if err:
        return err

    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'msg': '用户不存在'}), 404

    start, end = stats_service.week_range()
    weekly_stats = stats_service.weekly_stats(user.user_id, end=end)
    weight_records = stats_service.weight_records_between(user.user_id, start, end)

    diseases = load_user_diseases(user.user_id)

    try:
        result = generate_weekly_report(user.to_dict(), weekly_stats, weight_records, diseases)
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'AI周报生成失败: {str(e)}'}), 500

    weight_diff = stats_service.weight_diff(weight_records)

    report = AiReport(
        user_id=user.user_id,
        start_date=start,
        end_date=end,
        total_cal=weekly_stats['total_cal'],
        avg_daily_cal=round(weekly_stats['total_cal'] / 7),
        weight_diff=weight_diff,
        ai_comment=result['ai_comment'],
        suggest=result['suggest'],
    )
    db.session.add(report)
    db.session.commit()
    db.session.refresh(report)

    return jsonify({'code': 200, 'msg': '周报生成成功', 'data': report.to_dict()}), 200


@api.route('/ai/report', methods=['GET'])
@auth_required
def list_ai_reports():
    user_id, err = resolve_user_id(request.args.get('user_id', type=int))
    if err:
        return err

    limit = request.args.get('limit', 5, type=int)
    reports = AiReport.query.filter_by(user_id=user_id) \
        .order_by(AiReport.created_at.desc()) \
        .limit(limit).all()
    return jsonify({'code': 200, 'data': [r.to_dict() for r in reports]})


@api.route('/ai/plan/<int:plan_id>', methods=['DELETE'])
@auth_required
def delete_ai_plan(plan_id):
    plan = AiDietPlan.query.get(plan_id)
    if not plan:
        return jsonify({'code': 404, 'msg': '方案不存在'}), 404
    err = ensure_owner(plan)
    if err:
        return err
    db.session.delete(plan)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '方案已删除'})


@api.route('/ai/report/<int:report_id>', methods=['DELETE'])
@auth_required
def delete_ai_report(report_id):
    report = AiReport.query.get(report_id)
    if not report:
        return jsonify({'code': 404, 'msg': '周报不存在'}), 404
    err = ensure_owner(report)
    if err:
        return err
    db.session.delete(report)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '周报已删除'})
