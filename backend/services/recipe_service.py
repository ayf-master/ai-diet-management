"""食谱用例：创建/更新/删除、可见性、展示热量、烹饪偏好。

route 只负责 HTTP 参数与身份；这里负责业务规则、查询、事务边界。
"""
from sqlalchemy import func, or_

from app import db
from models import CookingMethod, Food, Recipe, RecipeFood, UserCookingPref
from services import nutrition
from services.errors import DomainError
from services.health_check import evaluate_recipe, load_user_disease_rules
from utils.auth import can_edit_owner, can_view_owner


def _num(value, default=0.0):
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _validated_name(data):
    if not isinstance(data, dict):
        raise DomainError(400, '请求数据为空')
    name = (data.get('recipe_name') or '').strip()
    if not name:
        raise DomainError(400, '食谱名称不能为空')
    return name


def _duplicate_recipe(name, owner_id, exclude_id=None):
    """同名食谱查重：普通用户查“系统 + 自己”，管理员查全局。"""
    q = Recipe.query.filter(
        func.lower(func.trim(Recipe.recipe_name)) == (name or '').strip().lower()
    )
    if owner_id is not None:
        q = q.filter(or_(Recipe.user_id.is_(None), Recipe.user_id == owner_id))
    if exclude_id is not None:
        q = q.filter(Recipe.recipe_id != exclude_id)
    return q.first()


def _cook_method_coefficients(cook_method):
    if not cook_method:
        return 0.0, 0.0
    cm = db.session.get(CookingMethod, cook_method)
    if not cm:
        return 0.0, 0.0
    return _num(cm.oil_per_100g), _num(cm.sauce_kcal_per_100g)


def _apply_totals(recipe, ingredients):
    oil_per_100g, sauce_kcal_per_100g = _cook_method_coefficients(recipe.cook_method)
    totals = nutrition.calc_recipe_totals(
        ingredients,
        oil_g=recipe.oil_g,
        sauce_g=recipe.sauce_g,
        oil_per_100g=oil_per_100g,
        sauce_kcal_per_100g=sauce_kcal_per_100g,
    )
    recipe.total_weight = totals.total_weight
    recipe.base_calorie = totals.base_calorie
    recipe.added_calorie = totals.added_calorie
    recipe.total_calorie = totals.total_calorie


def _replace_recipe_foods(recipe, ingredients, *, replace):
    """写入 RecipeFood 并返回纯计算所需的 IngredientNutrition 列表。"""
    if ingredients is None:
        ingredients = []
    if not isinstance(ingredients, list):
        raise DomainError(400, 'ingredients 必须是数组')

    if replace:
        RecipeFood.query.filter_by(recipe_id=recipe.recipe_id).delete()

    inputs = []
    for item in ingredients:
        if not isinstance(item, dict) or not item.get('food_id'):
            raise DomainError(400, '食材参数错误：缺少 food_id')
        food = db.session.get(Food, item['food_id'])
        if not food:
            raise DomainError(400, f'食材 {item["food_id"]} 不存在')
        weight = _num(item.get('weight'))
        db.session.add(RecipeFood(
            recipe_id=recipe.recipe_id,
            food_id=food.food_id,
            weight=weight,
        ))
        inputs.append(nutrition.IngredientNutrition(
            weight=weight,
            calorie_per_100g=food.nutrition.calorie if food.nutrition else None,
        ))
    return inputs


def _existing_ingredient_inputs(recipe):
    inputs = []
    for rf in RecipeFood.query.filter_by(recipe_id=recipe.recipe_id).all():
        food = db.session.get(Food, rf.food_id)
        inputs.append(nutrition.IngredientNutrition(
            weight=_num(rf.weight),
            calorie_per_100g=food.nutrition.calorie if food and food.nutrition else None,
        ))
    return inputs


def create_recipe(data, *, owner_id, admin_id):
    name = _validated_name(data)
    if _duplicate_recipe(name, owner_id):
        raise DomainError(409, f'食谱「{name}」已存在，请勿重复添加')

    recipe = Recipe(
        admin_id=admin_id,
        user_id=owner_id,
        recipe_name=name,
        type=data.get('type', '午餐'),
        suitable_goals=data.get('suitable_goals', 'healthy'),
        intro=data.get('intro'),
        cook_method=data.get('cook_method', '炒'),
        forbid_tips=data.get('forbid_tips'),
        oil_g=_num(data.get('oil_g')),
        sauce_g=_num(data.get('sauce_g')),
    )

    try:
        db.session.add(recipe)
        db.session.flush()
        inputs = _replace_recipe_foods(
            recipe, data.get('ingredients', []), replace=False
        )
        _apply_totals(recipe, inputs)
        db.session.commit()
        db.session.refresh(recipe)
        return recipe
    except Exception:
        db.session.rollback()
        raise


def update_recipe(recipe_id, data, *, viewer_id, viewer_is_admin):
    recipe = get_editable_recipe(recipe_id, viewer_id, viewer_is_admin)
    if not isinstance(data, dict) or not data:
        raise DomainError(400, '请求数据为空')

    new_name = (data.get('recipe_name') or recipe.recipe_name or '').strip()
    if _duplicate_recipe(new_name, recipe.user_id, exclude_id=recipe_id):
        raise DomainError(409, f'食谱「{new_name}」已存在，无法改名成重复名称')

    for field in (
        'recipe_name', 'type', 'suitable_goals', 'intro', 'cook_method',
        'forbid_tips', 'oil_g', 'sauce_g',
    ):
        if field in data:
            setattr(recipe, field, data[field] or 0)

    try:
        if 'ingredients' in data:
            inputs = _replace_recipe_foods(recipe, data['ingredients'], replace=True)
            _apply_totals(recipe, inputs)
        elif 'cook_method' in data:
            # 只改烹饪方式：用现有食材重算基础热量，再叠加新做法附加热量
            _apply_totals(recipe, _existing_ingredient_inputs(recipe))

        db.session.commit()
        db.session.refresh(recipe)
        return recipe
    except Exception:
        db.session.rollback()
        raise


def delete_recipe(recipe_id, *, viewer_id, viewer_is_admin):
    recipe = get_editable_recipe(recipe_id, viewer_id, viewer_is_admin)
    try:
        RecipeFood.query.filter_by(recipe_id=recipe_id).delete()
        db.session.delete(recipe)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise DomainError(400, '该食谱被打卡记录引用，无法删除')


def get_editable_recipe(recipe_id, viewer_id, viewer_is_admin):
    recipe = db.session.get(Recipe, recipe_id)
    if not recipe:
        raise DomainError(404, '食谱不存在')
    if not can_edit_owner(recipe.user_id, viewer_id, viewer_is_admin):
        if recipe.user_id is None:
            raise DomainError(403, '系统数据仅管理员可修改')
        raise DomainError(403, '无权操作该食谱')
    return recipe


def load_user_cooking_prefs(user_id):
    if not user_id:
        return {}
    prefs = UserCookingPref.query.filter_by(user_id=user_id).all()
    return {p.cook_method: p for p in prefs}


def recipe_payload(recipe, user_prefs=None):
    """展示用热量：保留“用户偏好覆盖烹饪方式”的旧逻辑，但不写库。"""
    data = recipe.to_dict()
    base = recipe.base_calorie or 0

    if recipe.oil_g or recipe.sauce_g:
        added = nutrition.added_calories_from_grams(recipe.oil_g, recipe.sauce_g)
        data['added_calorie'] = added
        data['total_calorie'] = round(base + added)
        return data

    cm = (user_prefs or {}).get(recipe.cook_method)
    if cm is not None and recipe.total_weight:
        added_raw = nutrition.added_calories_from_cook_method_raw(
            recipe.total_weight, cm.oil_per_100g, cm.sauce_kcal_per_100g
        )
        data['added_calorie'] = round(added_raw)
        data['total_calorie'] = round(base + added_raw)
    return data


def list_recipes(
    *,
    goal='',
    goals='',
    meal_type='',
    keyword='',
    scope_user_id=None,
    viewer_id=None,
    viewer_is_admin=False,
):
    query = Recipe.query
    if not viewer_is_admin:
        query = query.filter(
            or_(Recipe.user_id.is_(None), Recipe.user_id == viewer_id)
        )

    if goals:
        goal_list = [g.strip() for g in goals.split(',') if g.strip()]
        if goal_list:
            query = query.filter(
                or_(*[Recipe.suitable_goals.like(f'%{g}%') for g in goal_list])
            )
    elif goal:
        query = query.filter(Recipe.suitable_goals.like(f'%{goal}%'))
    if meal_type:
        query = query.filter_by(type=meal_type)
    if keyword:
        query = query.filter(Recipe.recipe_name.like(f'%{keyword}%'))

    recipes = query.order_by(Recipe.recipe_id).all()
    prefs = load_user_cooking_prefs(scope_user_id)
    data = [recipe_payload(r, prefs) for r in recipes]

    if scope_user_id:
        diseases = load_user_disease_rules(scope_user_id)
        if diseases:
            for recipe, item in zip(recipes, data):
                item['health_warning'] = evaluate_recipe(recipe, diseases)
    return data


def get_recipe_payload(recipe_id, *, scope_user_id=None, viewer_id=None, viewer_is_admin=False):
    recipe = db.session.get(Recipe, recipe_id)
    if not recipe or not can_view_owner(recipe.user_id, viewer_id, viewer_is_admin):
        raise DomainError(404, '食谱不存在')
    prefs = load_user_cooking_prefs(scope_user_id)
    return recipe_payload(recipe, prefs)


def list_cooking_methods():
    methods = CookingMethod.query.order_by(CookingMethod.cook_method).all()
    return [m.cook_method for m in methods]


def get_cooking_prefs(user_id):
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
    return data


def save_cooking_prefs(user_id, prefs):
    UserCookingPref.query.filter_by(user_id=user_id).delete()
    for item in prefs or []:
        cook_method = item.get('cook_method') if isinstance(item, dict) else None
        if not cook_method:
            continue
        up = UserCookingPref(user_id=user_id, cook_method=cook_method)
        up.oil_per_100g = _num(item.get('oil_per_100g'))
        up.sauce_kcal_per_100g = _num(item.get('sauce_kcal_per_100g'))
        db.session.add(up)
    db.session.commit()


def reset_cooking_prefs(user_id):
    UserCookingPref.query.filter_by(user_id=user_id).delete()
    db.session.commit()
