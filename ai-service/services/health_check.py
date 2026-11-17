"""按用户所选疾病判定食材/食谱是否对其有害（系统与自建食材共用同一逻辑）。"""
import json
from db import db
from models import Disease, UserDisease

# 风险等级与含义：ok=安全, warn=需注意, danger=不建议
_LEVEL_ORDER = {'ok': 0, 'warn': 1, 'danger': 2}
_NUTRI_FIELDS = ('calorie', 'protein', 'fat', 'carbohydrate', 'fiber', 'sugar', 'sodium')


def _upgrade(cur, new):
    """返回两者中更严重的一级。"""
    return new if _LEVEL_ORDER.get(new, 0) > _LEVEL_ORDER.get(cur, 0) else cur


def load_user_disease_rules(user_id):
    """取出该用户所选疾病的判定规则，返回 [{name, keywords:[], rules:{}}, ...]。"""
    if not user_id:
        return []
    uds = UserDisease.query.filter_by(user_id=user_id).all()
    out = []
    for ud in uds:
        d = Disease.query.get(ud.disease_id)
        if not d:
            continue
        keywords = [k.strip() for k in (d.forbid_keywords or '').split(',') if k.strip()]
        rules = {}
        if d.forbid_rules:
            try:
                rules = json.loads(d.forbid_rules)
            except Exception:
                rules = {}
        out.append({'name': d.disease_name, 'keywords': keywords, 'rules': rules})
    return out


def load_user_diseases(user_id):
    """取用户疾病 ORM 对象，并把用户级备注注入，供 AI prompt 使用。"""
    if not user_id:
        return []
    diseases = []
    for ud in UserDisease.query.filter_by(user_id=user_id).all():
        disease = db.session.get(Disease, ud.disease_id)
        if disease:
            disease.remark = ud.remark
            diseases.append(disease)
    return diseases


def evaluate_nutrition(name, nutrition, diseases):
    """对一份「每100g营养」做判定，返回 {level, reasons:[...]}。"""
    if not diseases:
        return {'level': 'ok', 'reasons': []}
    name = name or ''
    n = nutrition or {}
    level, reasons = 'ok', []
    for d in diseases:
        # 名称关键词匹配
        for kw in d['keywords']:
            if kw and kw in name:
                reasons.append(f'{d["name"]}：名称含「{kw}」')
                level = _upgrade(level, 'warn')
        # ② 营养阈值（每100g）
        r = d['rules'] or {}
        sugar = (n.get('sugar') or 0)
        sodium = (n.get('sodium') or 0)
        fat = (n.get('fat') or 0)
        carb = (n.get('carbohydrate') or 0)
        if r.get('max_sugar') is not None and sugar > r['max_sugar']:
            reasons.append(f'{d["name"]}：糖分过高（{sugar}g/100g）')
            level = _upgrade(level, 'warn')
        if r.get('max_sodium') is not None and sodium > r['max_sodium']:
            reasons.append(f'{d["name"]}：钠偏高（{sodium}mg/100g）')
            level = _upgrade(level, 'warn')
        if r.get('max_fat') is not None and fat > r['max_fat']:
            reasons.append(f'{d["name"]}：脂肪偏高（{fat}g/100g）')
            level = _upgrade(level, 'danger')
        if r.get('max_carbohydrate') is not None and carb > r['max_carbohydrate']:
            reasons.append(f'{d["name"]}：碳水偏高（{carb}g/100g）')
            level = _upgrade(level, 'warn')
    return {'level': level, 'reasons': reasons}


def _nutri_dict(food):
    """从 Food ORM 对象取营养字典；没有则返回空字典。"""
    if food and getattr(food, 'nutrition', None):
        return food.nutrition.to_dict()
    return {}


def evaluate_food(food, diseases):
    """判定单个食材（Food ORM 对象或带 nutrition 的 dict）。"""
    if isinstance(food, dict):
        return evaluate_nutrition(food.get('food_name'), food.get('nutrition') or {}, diseases)
    name = food.food_name if hasattr(food, 'food_name') else ''
    return evaluate_nutrition(name, _nutri_dict(food), diseases)


def evaluate_recipe(recipe, diseases):
    """判定食谱：先把食材配比加权聚合成总营养，再折算成每100g后判定。"""
    if not diseases:
        return {'level': 'ok', 'reasons': []}
    total = {k: 0.0 for k in _NUTRI_FIELDS}
    total_w = 0.0
    ingredients = recipe.ingredients if hasattr(recipe, 'ingredients') else recipe.get('ingredients') or []
    for rf in ingredients:
        food = rf.food if hasattr(rf, 'food') else None
        w = (rf.weight if hasattr(rf, 'weight') else rf.get('weight')) or 0
        total_w += w
        if food and getattr(food, 'nutrition', None):
            nd = food.nutrition.to_dict()
            for k in _NUTRI_FIELDS:
                total[k] += (nd.get(k) or 0) * w / 100.0
    per100 = {}
    if total_w > 0:
        for k in _NUTRI_FIELDS:
            per100[k] = round(total[k] / total_w * 100, 2)
    name = recipe.recipe_name if hasattr(recipe, 'recipe_name') else recipe.get('recipe_name', '')
    return evaluate_nutrition(name, per100, diseases)
