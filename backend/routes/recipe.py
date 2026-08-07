from flask import request, jsonify
from app import db
from sqlalchemy import or_
from models import Recipe, RecipeFood, Food, CookingMethod, UserCookingPref
from services.health_check import evaluate_recipe, load_user_disease_rules
from . import api

OIL_KCAL_PER_G = 9.0    # kcal/g
SAUCE_KCAL_PER_G = 4.0  # kcal/g


def _added_from_grams(oil_g, sauce_g):
    """用户直接填写的绝对克数 → 附加热量（kcal）。"""
    return round((oil_g or 0) * OIL_KCAL_PER_G + (sauce_g or 0) * SAUCE_KCAL_PER_G)


def _calc_calories(cook_method, total_weight, base_calorie):
    """按烹饪方式算附加热量，返回 (added, total)。"""
    added = 0.0
    if cook_method and total_weight:
        cm = CookingMethod.query.get(cook_method)
        if cm:
            oil_cal = (cm.oil_per_100g or 0) * total_weight / 100.0 * OIL_KCAL_PER_G
            sauce_cal = (cm.sauce_kcal_per_100g or 0) * total_weight / 100.0
            added = oil_cal + sauce_cal
    return round(added), round(base_calorie + added)


def _load_user_cooking_prefs(user_id):
    """返回 {cook_method: UserCookingPref}，该用户对各做法的个性化覆盖值。"""
    if not user_id:
        return {}
    prefs = UserCookingPref.query.filter_by(user_id=user_id).all()
    return {p.cook_method: p for p in prefs}


def _recipe_dict_for_user(recipe, user_prefs):
    """返回食谱字典，按优先级算附加热量（不改库）。"""
    d = recipe.to_dict()
    if recipe.oil_g or recipe.sauce_g:
        added = _added_from_grams(recipe.oil_g, recipe.sauce_g)
        d['added_calorie'] = added
        d['total_calorie'] = round((recipe.base_calorie or 0) + added)
        return d
    cm = user_prefs.get(recipe.cook_method)
    if cm is not None and recipe.total_weight:
        oil = (cm.oil_per_100g or 0) * recipe.total_weight / 100.0 * OIL_KCAL_PER_G
        sauce = (cm.sauce_kcal_per_100g or 0) * recipe.total_weight / 100.0
        added = oil + sauce
        d['added_calorie'] = round(added)
        d['total_calorie'] = round((recipe.base_calorie or 0) + added)
    return d


@api.route('/recipes', methods=['GET'])
def list_recipes():
    goal = request.args.get('goal', '')
    goals = request.args.get('goals', '')
    meal_type = request.args.get('type', '')
    keyword = request.args.get('keyword', '')
    user_id = request.args.get('user_id', type=int)

    query = Recipe.query
    if goals:
        goal_list = [g.strip() for g in goals.split(',') if g.strip()]
        if goal_list:
            query = query.filter(or_(*[Recipe.suitable_goals.like(f'%{g}%') for g in goal_list]))
    elif goal:
        query = query.filter(Recipe.suitable_goals.like(f'%{goal}%'))
    if meal_type:
        query = query.filter_by(type=meal_type)
    if keyword:
        query = query.filter(Recipe.recipe_name.like(f'%{keyword}%'))
    if user_id:
        query = query.filter(or_(Recipe.user_id.is_(None), Recipe.user_id == user_id))

    recipes = query.order_by(Recipe.recipe_id).all()
    user_prefs = _load_user_cooking_prefs(user_id)
    data = [_recipe_dict_for_user(r, user_prefs) for r in recipes]
    # 若带 user_id，根据用户所选疾病给每项附加健康警告（系统/自建食谱共用同一判定）
    if user_id:
        diseases = load_user_disease_rules(user_id)
        if diseases:
            for r, d in zip(recipes, data):
                d['health_warning'] = evaluate_recipe(r, diseases)
    return jsonify({'code': 200, 'data': data})


@api.route('/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        return jsonify({'code': 404, 'msg': '食谱不存在'}), 404
    user_id = request.args.get('user_id', type=int)
    user_prefs = _load_user_cooking_prefs(user_id)
    return jsonify({'code': 200, 'data': _recipe_dict_for_user(recipe, user_prefs)})


@api.route('/cooking-methods', methods=['GET'])
def list_cooking_methods():
    """返回所有烹饪方式，供前端新增/编辑食谱时下拉选择。"""
    methods = CookingMethod.query.order_by(CookingMethod.cook_method).all()
    return jsonify({'code': 200, 'data': [m.cook_method for m in methods]})


@api.route('/recipes', methods=['POST'])
def create_recipe():
    data = request.get_json()
    if not data or not data.get('recipe_name'):
        return jsonify({'code': 400, 'msg': '食谱名称不能为空'}), 400

    recipe = Recipe(
        admin_id=data.get('admin_id'),
        user_id=data.get('user_id'),
        recipe_name=data['recipe_name'],
        type=data.get('type', '午餐'),
        suitable_goals=data.get('suitable_goals', 'healthy'),
        intro=data.get('intro'),
        cook_method=data.get('cook_method', '炒'),
        forbid_tips=data.get('forbid_tips'),
        oil_g=data.get('oil_g') or 0,
        sauce_g=data.get('sauce_g') or 0,
    )
    db.session.add(recipe)
    db.session.flush()

    total_weight = 0.0
    base_calorie = 0.0
    for ing in data.get('ingredients', []):
        food = Food.query.get(ing['food_id'])
        weight = ing.get('weight') or 0
        total_weight += weight
        if food and food.nutrition:
            base_calorie += food.nutrition.calorie * weight / 100.0
        rf = RecipeFood(
            recipe_id=recipe.recipe_id,
            food_id=ing['food_id'],
            weight=weight,
        )
        db.session.add(rf)

    recipe.total_weight = total_weight
    recipe.base_calorie = round(base_calorie)
    # 优先用用户填的绝对克数；否则回退烹饪方式系数
    if recipe.oil_g or recipe.sauce_g:
        added_calorie = _added_from_grams(recipe.oil_g, recipe.sauce_g)
    else:
        added_calorie, _ = _calc_calories(recipe.cook_method, total_weight, base_calorie)
    recipe.added_calorie = added_calorie
    recipe.total_calorie = round(base_calorie + added_calorie)
    db.session.commit()
    db.session.refresh(recipe)
    return jsonify({'code': 200, 'msg': '创建成功', 'data': recipe.to_dict()}), 200


@api.route('/recipes/<int:recipe_id>', methods=['PUT'])
def update_recipe(recipe_id):
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        return jsonify({'code': 404, 'msg': '食谱不存在'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'msg': '请求数据为空'}), 400

    for field in ('recipe_name', 'type', 'suitable_goals', 'intro', 'cook_method', 'forbid_tips', 'oil_g', 'sauce_g'):
        if field in data:
            setattr(recipe, field, data[field] or 0)

    # 替换食材配比（先删后加），重算生食材热量/总重量/附加热量
    if 'ingredients' in data:
        RecipeFood.query.filter_by(recipe_id=recipe_id).delete()
        total_weight = 0.0
        base_calorie = 0.0
        for ing in data['ingredients']:
            food = Food.query.get(ing['food_id'])
            weight = ing.get('weight') or 0
            total_weight += weight
            if food and food.nutrition:
                base_calorie += food.nutrition.calorie * weight / 100.0
            rf = RecipeFood(
                recipe_id=recipe.recipe_id,
                food_id=ing['food_id'],
                weight=weight,
            )
            db.session.add(rf)
        recipe.total_weight = total_weight
        recipe.base_calorie = round(base_calorie)
        if recipe.oil_g or recipe.sauce_g:
            added_calorie = _added_from_grams(recipe.oil_g, recipe.sauce_g)
        else:
            added_calorie, _ = _calc_calories(recipe.cook_method, total_weight, base_calorie)
        recipe.added_calorie = added_calorie
        recipe.total_calorie = round(base_calorie + added_calorie)
    elif 'cook_method' in data:
        # 仅改烹饪方式：用现有食材重算生食材热量，再叠加新做法附加热量
        total_weight = 0.0
        base_calorie = 0.0
        for rf in RecipeFood.query.filter_by(recipe_id=recipe_id).all():
            food = Food.query.get(rf.food_id)
            weight = rf.weight or 0
            total_weight += weight
            if food and food.nutrition:
                base_calorie += food.nutrition.calorie * weight / 100.0
        recipe.total_weight = total_weight
        recipe.base_calorie = round(base_calorie)
        if recipe.oil_g or recipe.sauce_g:
            added_calorie = _added_from_grams(recipe.oil_g, recipe.sauce_g)
        else:
            added_calorie, _ = _calc_calories(recipe.cook_method, total_weight, base_calorie)
        recipe.added_calorie = added_calorie
        recipe.total_calorie = round(base_calorie + added_calorie)

    db.session.commit()
    db.session.refresh(recipe)
    return jsonify({'code': 200, 'msg': '更新成功', 'data': recipe.to_dict()})


@api.route('/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        return jsonify({'code': 404, 'msg': '食谱不存在'}), 404

    try:
        RecipeFood.query.filter_by(recipe_id=recipe_id).delete()
        db.session.delete(recipe)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '删除成功'})
    except Exception:
        db.session.rollback()
        return jsonify({'code': 400, 'msg': '该食谱被打卡记录引用，无法删除'}), 400


@api.route('/user-cooking-prefs', methods=['GET'])
def get_user_cooking_prefs():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'code': 400, 'msg': '缺少user_id'}), 400
    methods = CookingMethod.query.order_by(CookingMethod.cook_method).all()
    prefs = {p.cook_method: p for p in UserCookingPref.query.filter_by(user_id=user_id).all()}
    data = []
    for cm in methods:
        up = prefs.get(cm.cook_method)
        data.append({
            'cook_method': cm.cook_method,
            'oil_per_100g': up.oil_per_100g if up else cm.oil_per_100g,
            'sauce_kcal_per_100g': up.sauce_kcal_per_100g if up else cm.sauce_kcal_per_100g,
            'is_custom': up is not None,
        })
    return jsonify({'code': 200, 'data': data})


@api.route('/user-cooking-prefs', methods=['PUT'])
def save_user_cooking_prefs():
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'code': 400, 'msg': '缺少user_id'}), 400
    # 替换该用户全部偏好：先删后插
    UserCookingPref.query.filter_by(user_id=user_id).delete()
    for it in data.get('prefs', []):
        cm = it.get('cook_method')
        if not cm:
            continue
        up = UserCookingPref(user_id=user_id, cook_method=cm)
        up.oil_per_100g = float(it.get('oil_per_100g') or 0)
        up.sauce_kcal_per_100g = float(it.get('sauce_kcal_per_100g') or 0)
        db.session.add(up)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '保存成功'})


@api.route('/user-cooking-prefs', methods=['DELETE'])
def reset_user_cooking_prefs():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'code': 400, 'msg': '缺少user_id'}), 400
    UserCookingPref.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return jsonify({'code': 200, 'msg': '已重置为默认'})
