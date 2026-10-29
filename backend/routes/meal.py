"""打卡/统计路由：HTTP 参数与身份校验，业务在 meal_service / stats_service。"""
from flask import request, jsonify

from services import meal_service, stats_service
from utils.auth import auth_required, current_user_id, is_admin, resolve_user_id
from . import api


@api.route('/meal-types', methods=['GET'])
@auth_required
def list_meal_types():
    return jsonify({'code': 200, 'data': meal_service.list_meal_types()})


@api.route('/meals', methods=['POST'])
@auth_required
def create_meal():
    data = request.get_json() or {}
    user_id, err = resolve_user_id(data.get('user_id'))
    if err:
        return err

    record = meal_service.create_meal(data, user_id=user_id)
    return jsonify({'code': 200, 'msg': '打卡成功', 'data': record.to_dict()}), 200


@api.route('/meals', methods=['GET'])
@auth_required
def list_meals():
    user_id, err = resolve_user_id(request.args.get('user_id', type=int))
    if err:
        return err

    records = meal_service.list_meals(user_id, request.args.get('date', ''))
    return jsonify({'code': 200, 'data': [r.to_dict() for r in records]})


@api.route('/meals/<int:record_id>', methods=['DELETE'])
@auth_required
def delete_meal(record_id):
    meal_service.delete_meal(
        record_id,
        viewer_id=current_user_id(),
        viewer_is_admin=is_admin(),
    )
    return jsonify({'code': 200, 'msg': '删除成功'})


@api.route('/stats/daily', methods=['GET'])
@auth_required
def daily_stats():
    user_id, err = resolve_user_id(request.args.get('user_id', type=int))
    if err:
        return err

    data = stats_service.daily_stats(user_id, request.args.get('date'))
    return jsonify({'code': 200, 'data': data})


@api.route('/stats/weekly', methods=['GET'])
@auth_required
def weekly_stats():
    user_id, err = resolve_user_id(request.args.get('user_id', type=int))
    if err:
        return err

    data = stats_service.weekly_stats(user_id)
    return jsonify({'code': 200, 'data': data})
