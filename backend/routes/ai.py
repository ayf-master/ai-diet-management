from datetime import date, timedelta
from flask import request, jsonify
from app import db
from models import User, UserDisease, Disease, AiDietPlan, AiReport, DietRecord
from services.ai_service import generate_diet_plan, generate_weekly_report, format_taboo_prompt
from . import api


@api.route('/ai/plan', methods=['POST'])
def create_ai_plan():
    data = request.get_json()
    if not data or not data.get('user_id'):
        return jsonify({'code': 400, 'msg': '缺少user_id'}), 400

    user = User.query.get(data['user_id'])
    if not user:
        return jsonify({'code': 404, 'msg': '用户不存在'}), 404

    user_diseases = UserDisease.query.filter_by(user_id=user.user_id).all()
    diseases = []
    for ud in user_diseases:
        disease = Disease.query.get(ud.disease_id)
        if disease:
            disease.remark = ud.remark  # 用户级个性化备注，注入 AI 上下文
            diseases.append(disease)

    try:
        result = generate_diet_plan(user.to_dict(), diseases)
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'AI方案生成失败: {str(e)}'}), 500

    if not result.get('plan_content') or not result['plan_content'].strip():
        return jsonify({'code': 500, 'msg': 'AI返回内容为空，请稍后重试'}), 500

    plan = AiDietPlan(
        user_id=user.user_id,
        create_date=date.today(),
        plan_content=result['plan_content'],
        forbid_food=format_taboo_prompt(diseases) if diseases else None,
        total_cal=result['total_cal'],
    )
    db.session.add(plan)
    db.session.commit()
    db.session.refresh(plan)

    return jsonify({'code': 200, 'msg': '方案生成成功', 'data': plan.to_dict()}), 200


@api.route('/ai/plan', methods=['GET'])
def list_ai_plans():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'code': 400, 'msg': '缺少user_id'}), 400

    limit = request.args.get('limit', 5, type=int)
    plans = AiDietPlan.query.filter_by(user_id=user_id)\
        .order_by(AiDietPlan.create_date.desc())\
        .limit(limit).all()
    return jsonify({'code': 200, 'data': [p.to_dict() for p in plans]})


@api.route('/ai/report', methods=['POST'])
def create_ai_report():
    data = request.get_json()
    if not data or not data.get('user_id'):
        return jsonify({'code': 400, 'msg': '缺少user_id'}), 400

    user = User.query.get(data['user_id'])
    if not user:
        return jsonify({'code': 404, 'msg': '用户不存在'}), 404

    end = date.today()
    start = end - timedelta(days=6)

    records = DietRecord.query.filter(
        DietRecord.user_id == user.user_id,
        DietRecord.eat_date.between(start, end)
    ).order_by(DietRecord.eat_date).all()

    daily_data = {}
    for r in records:
        day = str(r.eat_date)
        daily_data[day] = daily_data.get(day, 0) + r.total_cal

    week = [(start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    daily = [{'date': d, 'cal': daily_data.get(d, 0)} for d in week]

    weekly_stats = {
        'total_cal': sum(r.total_cal for r in records),
        'daily': daily,
    }

    from models import WeightRecord
    weight_records = WeightRecord.query.filter(
        WeightRecord.user_id == user.user_id,
        WeightRecord.measure_date.between(start, end)
    ).order_by(WeightRecord.measure_date).all()

    user_diseases = UserDisease.query.filter_by(user_id=user.user_id).all()
    diseases = []
    for ud in user_diseases:
        disease = Disease.query.get(ud.disease_id)
        if disease:
            disease.remark = ud.remark  # 用户级个性化备注，注入 AI 上下文
            diseases.append(disease)

    try:
        result = generate_weekly_report(user.to_dict(), weekly_stats, weight_records, diseases)
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'AI周报生成失败: {str(e)}'}), 500

    weight_diff = 0
    if weight_records and len(weight_records) >= 2:
        weight_diff = round(weight_records[-1].weight - weight_records[0].weight, 1)

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
def list_ai_reports():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'code': 400, 'msg': '缺少user_id'}), 400

    limit = request.args.get('limit', 5, type=int)
    reports = AiReport.query.filter_by(user_id=user_id)\
        .order_by(AiReport.created_at.desc())\
        .limit(limit).all()
    return jsonify({'code': 200, 'data': [r.to_dict() for r in reports]})


@api.route('/ai/plan/<int:plan_id>', methods=['DELETE'])
def delete_ai_plan(plan_id):
    plan = AiDietPlan.query.get(plan_id)
    if not plan:
        return jsonify({'code': 404, 'msg': '方案不存在'}), 404
    db.session.delete(plan)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '方案已删除'})


@api.route('/ai/report/<int:report_id>', methods=['DELETE'])
def delete_ai_report(report_id):
    report = AiReport.query.get(report_id)
    if not report:
        return jsonify({'code': 404, 'msg': '周报不存在'}), 404
    db.session.delete(report)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '周报已删除'})
