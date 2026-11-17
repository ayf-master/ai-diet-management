"""SQL 候选召回：只从数据库可见食谱中取闭集，模型不能凭空造食谱。"""
from sqlalchemy import text

from db import db
from models import Recipe
from services.health_check import evaluate_recipe

MEAL_LABELS = {
    'breakfast': '早餐',
    'lunch': '午餐',
    'dinner': '晚餐',
    'snack': '加餐',
}
MEAL_RATIOS = {
    'breakfast': 0.25,
    'lunch': 0.35,
    'dinner': 0.30,
    'snack': 0.10,
}

_CANDIDATE_SQL = """
SELECT
    recipe_id, recipe_name, type, suitable_goals, user_id,
    total_weight, total_calorie, protein_g, fat_g, carbohydrate_g,
    ingredient_count, calorie_per_100g, protein_per_100g
FROM v_recipe_nutrition
WHERE (user_id IS NULL OR user_id = :user_id)
  AND type = :meal_type
ORDER BY
    CASE WHEN suitable_goals LIKE :goal_pattern THEN 0 ELSE 1 END,
    ABS(total_calorie - :target_cal) ASC,
    recipe_id ASC
LIMIT :limit
"""


def _candidate_dict(row, health):
    return {
        'recipe_id': int(row['recipe_id']),
        'recipe_name': row['recipe_name'],
        'type': row['type'],
        'suitable_goals': row['suitable_goals'],
        'user_id': row['user_id'],
        'total_weight': float(row['total_weight'] or 0),
        'total_calorie': float(row['total_calorie'] or 0),
        'protein_g': float(row['protein_g'] or 0),
        'fat_g': float(row['fat_g'] or 0),
        'carbohydrate_g': float(row['carbohydrate_g'] or 0),
        'ingredient_count': int(row['ingredient_count'] or 0),
        'calorie_per_100g': float(row['calorie_per_100g'] or 0),
        'protein_per_100g': float(row['protein_per_100g'] or 0),
        'health_level': health.get('level', 'ok'),
        'health_reasons': health.get('reasons', []),
    }


def _health_map(recipe_ids, disease_rules):
    if not recipe_ids or not disease_rules:
        return {}
    recipes = Recipe.query.filter(Recipe.recipe_id.in_(recipe_ids)).all()
    return {
        recipe.recipe_id: evaluate_recipe(recipe, disease_rules)
        for recipe in recipes
    }


def recall_meal_candidates(user, meal_key, disease_rules=None, goal=None, limit=8):
    """召回单个餐次的候选；工具层也复用这一函数，避免两套 SQL。"""
    if meal_key not in MEAL_LABELS:
        return []
    target_total = float(user.recommend_cal or 1800)
    target_cal = target_total * MEAL_RATIOS[meal_key]
    goal_pattern = f"%{goal or user.diet_goal or 'healthy'}%"
    rows = db.session.execute(
        text(_CANDIDATE_SQL),
        {
            'user_id': user.user_id,
            'meal_type': MEAL_LABELS[meal_key],
            'goal_pattern': goal_pattern,
            'target_cal': target_cal,
            'limit': limit,
        },
    ).mappings().all()

    health = _health_map([r['recipe_id'] for r in rows], disease_rules)
    meal_candidates = []
    for row in rows:
        h = health.get(row['recipe_id'], {'level': 'ok', 'reasons': []})
        if h.get('level') == 'danger':
            continue
        meal_candidates.append(_candidate_dict(row, h))
    return meal_candidates


def recall_candidates(user, disease_rules=None, per_meal=8):
    """按餐次召回路程：可见 + 目标匹配优先 + 热量接近该餐目标。"""
    return {
        meal_key: recall_meal_candidates(
            user, meal_key, disease_rules=disease_rules, limit=per_meal,
        )
        for meal_key in MEAL_LABELS
    }


def candidate_count(candidates):
    return sum(len(items) for items in candidates.values())
