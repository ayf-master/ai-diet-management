"""食谱路由：只做 HTTP 适配，业务规则在 services/recipe_service.py。"""
from flask import request, jsonify

from services import recipe_service
from utils.auth import (
    auth_required,
    current_admin_id,
    current_user_id,
    ensure_self,
    is_admin,
)
from . import api


@api.route('/recipes', methods=['GET'])
@auth_required
def list_recipes():
    user_id = request.args.get('user_id', type=int)
    if user_id:
        err = ensure_self(user_id)
        if err:
            return err

    data = recipe_service.list_recipes(
        goal=request.args.get('goal', ''),
        goals=request.args.get('goals', ''),
        meal_type=request.args.get('type', ''),
        keyword=request.args.get('keyword', ''),
        scope_user_id=user_id,
        viewer_id=current_user_id(),
        viewer_is_admin=is_admin(),
    )
    return jsonify({'code': 200, 'data': data})


@api.route('/recipes/<int:recipe_id>', methods=['GET'])
@auth_required
def get_recipe(recipe_id):
    user_id = request.args.get('user_id', type=int)
    if user_id:
        err = ensure_self(user_id)
        if err:
            return err

    data = recipe_service.get_recipe_payload(
        recipe_id,
        scope_user_id=user_id,
        viewer_id=current_user_id(),
        viewer_is_admin=is_admin(),
    )
    return jsonify({'code': 200, 'data': data})


@api.route('/cooking-methods', methods=['GET'])
@auth_required
def list_cooking_methods():
    return jsonify({'code': 200, 'data': recipe_service.list_cooking_methods()})


@api.route('/recipes', methods=['POST'])
@auth_required
def create_recipe():
    data = request.get_json() or {}

    owner_id = data.get('user_id')
    if owner_id is not None:
        err = ensure_self(owner_id)
        if err:
            return err
        admin_id = None
    elif is_admin():
        # 管理员创建系统食谱，归属人取 token，不接受前端伪造 admin_id
        admin_id = current_admin_id()
        owner_id = None
    else:
        # 普通用户省略 user_id 时默认创建自己的食谱
        owner_id = current_user_id()
        admin_id = None

    recipe = recipe_service.create_recipe(data, owner_id=owner_id, admin_id=admin_id)
    return jsonify({'code': 200, 'msg': '创建成功', 'data': recipe.to_dict()}), 200


@api.route('/recipes/<int:recipe_id>', methods=['PUT'])
@auth_required
def update_recipe(recipe_id):
    recipe = recipe_service.update_recipe(
        recipe_id,
        request.get_json() or {},
        viewer_id=current_user_id(),
        viewer_is_admin=is_admin(),
    )
    return jsonify({'code': 200, 'msg': '更新成功', 'data': recipe.to_dict()}), 200


@api.route('/recipes/<int:recipe_id>', methods=['DELETE'])
@auth_required
def delete_recipe(recipe_id):
    recipe_service.delete_recipe(
        recipe_id,
        viewer_id=current_user_id(),
        viewer_is_admin=is_admin(),
    )
    return jsonify({'code': 200, 'msg': '删除成功'})


@api.route('/user-cooking-prefs', methods=['GET'])
@auth_required
def get_user_cooking_prefs():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'code': 400, 'msg': '缺少user_id'}), 400
    err = ensure_self(user_id)
    if err:
        return err
    return jsonify({'code': 200, 'data': recipe_service.get_cooking_prefs(user_id)})


@api.route('/user-cooking-prefs', methods=['PUT'])
@auth_required
def save_user_cooking_prefs():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'code': 400, 'msg': '缺少user_id'}), 400
    err = ensure_self(user_id)
    if err:
        return err

    recipe_service.save_cooking_prefs(user_id, data.get('prefs', []))
    return jsonify({'code': 200, 'msg': '保存成功'})


@api.route('/user-cooking-prefs', methods=['DELETE'])
@auth_required
def reset_user_cooking_prefs():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'code': 400, 'msg': '缺少user_id'}), 400
    err = ensure_self(user_id)
    if err:
        return err

    recipe_service.reset_cooking_prefs(user_id)
    return jsonify({'code': 200, 'msg': '已重置为默认'})
