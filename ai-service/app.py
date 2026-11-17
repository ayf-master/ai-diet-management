# AI 独立服务：只暴露内网 /ai/v1/**，由 Spring Boot 经内部 token 调用
import json
import logging
from datetime import date

from flask import Flask, jsonify, request

from config import INTERNAL_TOKEN, HOST, PORT
from db import db
from models import User, AiDietPlan, AiPlanRun, AiReport
from services.ai_service import generate_weekly_report, format_taboo_prompt
from services.agent.calling import run_single_turn
from services.errors import DomainError
from services.health_check import load_user_diseases
from services.planning.pipeline import generate_trusted_plan
from services import stats_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = __import__('config').SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    @app.before_request
    def check_internal_token():
        # 健康检查不鉴权；其余请求必须带内部 token
        if request.path == '/ai/v1/health':
            return None
        if request.headers.get('X-Internal-Token') != INTERNAL_TOKEN:
            return jsonify({'code': 401, 'msg': 'internal token invalid'}), 401
        return None

    @app.errorhandler(DomainError)
    def handle_domain_error(err):
        return jsonify({'code': err.code, 'msg': err.message}), err.code

    def get_user(user_id):
        return db.session.get(User, user_id)

    def acting_identity():
        # Spring 透传的当前登录者身份，用于删除类接口的归属校验
        raw_uid = request.headers.get('X-Acting-User-Id')
        uid = int(raw_uid) if raw_uid and raw_uid.isdigit() else None
        role = request.headers.get('X-Acting-Role', 'user')
        return uid, role

    def ensure_can_delete(owner_id):
        uid, role = acting_identity()
        if role == 'admin':
            return None
        if owner_id is None:
            return jsonify({'code': 403, 'msg': '系统数据仅管理员可修改'}), 403
        if uid is not None and int(owner_id) == uid:
            return None
        return jsonify({'code': 403, 'msg': '无权访问该资源'}), 403

    def meal_ids(selection, meal):
        return ','.join(str(dish.recipe_id) for dish in getattr(selection, meal))

    @app.get('/ai/v1/health')
    def health():
        return jsonify({'code': 200, 'data': {'service': 'ai', 'status': 'ok'}})

    @app.post('/ai/v1/plan')
    def create_plan():
        data = request.get_json(silent=True) or {}
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'code': 400, 'msg': '缺少 user_id'}), 400

        user = get_user(int(user_id))
        if not user:
            return jsonify({'code': 404, 'msg': '用户不存在'}), 404

        diseases = load_user_diseases(user.user_id)

        try:
            result = generate_trusted_plan(user, diseases)
        except DomainError:
            raise
        except Exception as e:
            logger.exception('AI方案生成失败')
            return jsonify({'code': 500, 'msg': f'AI方案生成失败: {str(e)}'}), 500

        if not result.plan or not result.verification.total_cal:
            return jsonify({'code': 500, 'msg': 'AI方案未生成有效内容，请稍后重试'}), 500

        plan = AiDietPlan(
            user_id=user.user_id,
            create_date=date.today(),
            plan_content=json.dumps(result.plan, ensure_ascii=False),
            breakfast_ids=meal_ids(result.selection, 'breakfast'),
            lunch_ids=meal_ids(result.selection, 'lunch'),
            dinner_ids=meal_ids(result.selection, 'dinner'),
            snack_ids=meal_ids(result.selection, 'snack'),
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

    @app.get('/ai/v1/plan')
    def list_plans():
        data = request.args
        user_id = data.get('user_id', type=int)
        if not user_id:
            return jsonify({'code': 400, 'msg': '缺少 user_id'}), 400
        limit = data.get('limit', 5, type=int)
        plans = AiDietPlan.query.filter_by(user_id=user_id) \
            .order_by(AiDietPlan.create_date.desc()) \
            .limit(limit).all()
        return jsonify({'code': 200, 'data': [p.to_dict() for p in plans]})

    @app.delete('/ai/v1/plan/<int:plan_id>')
    def delete_plan(plan_id):
        plan = db.session.get(AiDietPlan, plan_id)
        if not plan:
            return jsonify({'code': 404, 'msg': '方案不存在'}), 404
        err = ensure_can_delete(plan.user_id)
        if err:
            return err
        db.session.delete(plan)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '方案已删除'})

    @app.post('/ai/v1/assistant')
    def assistant():
        data = request.get_json(silent=True) or {}
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'code': 400, 'msg': '缺少 user_id'}), 400

        user = get_user(int(user_id))
        if not user:
            return jsonify({'code': 404, 'msg': '用户不存在'}), 404

        result = run_single_turn(user, data.get('message'))
        if result.status == 'invalid_request':
            http_status = 400
        elif result.status == 'unavailable':
            http_status = 503
        elif result.status == 'model_error':
            http_status = 502
        else:
            http_status = 200

        return jsonify({
            'code': http_status,
            'msg': '回答生成成功' if result.ok else '回答生成失败',
            'data': result.to_dict(),
        }), http_status

    @app.post('/ai/v1/report')
    def create_report():
        data = request.get_json(silent=True) or {}
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'code': 400, 'msg': '缺少 user_id'}), 400

        user = get_user(int(user_id))
        if not user:
            return jsonify({'code': 404, 'msg': '用户不存在'}), 404

        start, end = stats_service.week_range()
        weekly_stats = stats_service.weekly_stats(user.user_id, end=end)
        weight_records = stats_service.weight_records_between(user.user_id, start, end)
        diseases = load_user_diseases(user.user_id)

        try:
            result = generate_weekly_report(user.to_dict(), weekly_stats, weight_records, diseases)
        except Exception as e:
            logger.exception('AI周报生成失败')
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

    @app.get('/ai/v1/report')
    def list_reports():
        data = request.args
        user_id = data.get('user_id', type=int)
        if not user_id:
            return jsonify({'code': 400, 'msg': '缺少 user_id'}), 400
        limit = data.get('limit', 5, type=int)
        reports = AiReport.query.filter_by(user_id=user_id) \
            .order_by(AiReport.created_at.desc()) \
            .limit(limit).all()
        return jsonify({'code': 200, 'data': [r.to_dict() for r in reports]})

    @app.delete('/ai/v1/report/<int:report_id>')
    def delete_report(report_id):
        report = db.session.get(AiReport, report_id)
        if not report:
            return jsonify({'code': 404, 'msg': '周报不存在'}), 404
        err = ensure_can_delete(report.user_id)
        if err:
            return err
        db.session.delete(report)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '周报已删除'})

    return app


app = create_app()

if __name__ == '__main__':
    print(f'AI 服务启动于 http://{HOST}:{PORT}')
    app.run(debug=False, port=PORT, host=HOST, use_reloader=False)
