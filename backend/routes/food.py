from flask import request, jsonify
from sqlalchemy import func
from app import db
from models import Food, Nutrition, FoodCategory
from services.health_check import evaluate_food, load_user_disease_rules
from utils.auth import (
    auth_required,
    current_user_id,
    ensure_owner,
    ensure_self,
    is_admin,
    visible,
)
from . import api


def _dup_food(name, user_id, exclude_id=None):
    """判断同名食材是否已存在。作用域 = 该用户可见集合（系统食材 + 本人自建）；
    系统食材(user_id 空)则全局查重，避免任何用户看到重复。"""
    q = Food.query.filter(func.lower(func.trim(Food.food_name)) == (name or '').strip().lower())
    if user_id:
        q = q.filter(db.or_(Food.user_id.is_(None), Food.user_id == user_id))
    if exclude_id is not None:
        q = q.filter(Food.food_id != exclude_id)
    return q.first()


@api.route('/foods', methods=['GET'])
@auth_required
def list_foods():
    category_id = request.args.get('category_id', type=int)
    keyword = request.args.get('keyword', '')
    user_id = request.args.get('user_id', type=int)

    if user_id:
        err = ensure_self(user_id)
        if err:
            return err

    query = Food.query
    if not is_admin():
        # 普通用户只能看到系统食材 + 自己创建的食材
        uid = current_user_id()
        query = query.filter(db.or_(Food.user_id.is_(None), Food.user_id == uid))
    if category_id:
        query = query.filter_by(category_id=category_id)
    if keyword:
        query = query.filter(Food.food_name.like(f'%{keyword}%'))

    foods = query.order_by(Food.food_id).all()
    data = [f.to_dict() for f in foods]
    # 若带 user_id，根据用户所选疾病给每项附加健康警告（系统/自建食材共用同一判定）
    if user_id:
        diseases = load_user_disease_rules(user_id)
        if diseases:
            for f, d in zip(foods, data):
                d['health_warning'] = evaluate_food(f, diseases)
    return jsonify({'code': 200, 'data': data})


@api.route('/foods/<int:food_id>', methods=['GET'])
@auth_required
def get_food(food_id):
    food = Food.query.get(food_id)
    if not food or not visible(food):
        return jsonify({'code': 404, 'msg': '食材不存在'}), 404
    return jsonify({'code': 200, 'data': food.to_dict()})


@api.route('/foods', methods=['POST'])
@auth_required
def create_food():
    data = request.get_json()
    if not data or not data.get('food_name'):
        return jsonify({'code': 400, 'msg': '食材名称不能为空'}), 400

    owner_id = data.get('user_id')
    if owner_id is not None:
        err = ensure_self(owner_id)
        if err:
            return err
    elif not is_admin():
        return jsonify({'code': 403, 'msg': '只有管理员能创建系统食材'}), 403

    name = (data['food_name'] or '').strip()
    if _dup_food(name, owner_id):
        return jsonify({'code': 409, 'msg': f'食材「{name}」已存在，请勿重复添加'}), 409

    food = Food(
        food_name=data['food_name'],
        category_id=data.get('category_id', 1),
        unit=data.get('unit', '100g'),
        img_path=data.get('img_path'),
        user_id=owner_id,
    )
    db.session.add(food)
    db.session.flush()  # 获取 food_id

    nut = data.get('nutrition')
    if nut:
        nutrition = Nutrition(
            food_id=food.food_id,
            calorie=nut.get('calorie', 0),
            protein=nut.get('protein', 0),
            fat=nut.get('fat', 0),
            carbohydrate=nut.get('carbohydrate', 0),
            fiber=nut.get('fiber', 0),
            sugar=nut.get('sugar', 0),
            sodium=nut.get('sodium', 0),
        )
        db.session.add(nutrition)

    db.session.commit()
    food = Food.query.get(food.food_id)
    return jsonify({'code': 200, 'msg': '创建成功', 'data': food.to_dict()}), 200


@api.route('/foods/<int:food_id>', methods=['PUT'])
@auth_required
def update_food(food_id):
    food = Food.query.get(food_id)
    if not food:
        return jsonify({'code': 404, 'msg': '食材不存在'}), 404
    err = ensure_owner(food)
    if err:
        return err

    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'msg': '请求数据为空'}), 400

    new_name = (data.get('food_name') or food.food_name or '').strip()
    if _dup_food(new_name, food.user_id, exclude_id=food_id):
        return jsonify({'code': 409, 'msg': f'食材「{new_name}」已存在，无法改名成重复名称'}), 409

    for field in ('food_name', 'category_id', 'unit', 'img_path'):
        if field in data:
            setattr(food, field, data[field])

    nut = data.get('nutrition')
    if nut:
        if food.nutrition:
            for field in ('calorie', 'protein', 'fat', 'carbohydrate', 'fiber', 'sugar', 'sodium'):
                if field in nut:
                    setattr(food.nutrition, field, nut[field])
        else:
            nutrition = Nutrition(food_id=food.food_id, **nut)
            db.session.add(nutrition)

    db.session.commit()
    food = Food.query.get(food.food_id)
    return jsonify({'code': 200, 'msg': '更新成功', 'data': food.to_dict()})


@api.route('/foods/<int:food_id>', methods=['DELETE'])
@auth_required
def delete_food(food_id):
    food = Food.query.get(food_id)
    if not food:
        return jsonify({'code': 404, 'msg': '食材不存在'}), 404
    err = ensure_owner(food)
    if err:
        return err

    try:
        if food.nutrition:
            db.session.delete(food.nutrition)
        db.session.delete(food)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '删除成功'})
    except Exception:
        db.session.rollback()
        return jsonify({'code': 400, 'msg': '该食材被食谱引用，无法删除'}), 400


@api.route('/food-categories', methods=['GET'])
@auth_required
def list_categories():
    categories = FoodCategory.query.order_by(FoodCategory.sort_order).all()
    return jsonify({'code': 200, 'data': [c.to_dict() for c in categories]})
