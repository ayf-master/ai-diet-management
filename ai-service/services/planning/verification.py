"""数据库校验 + 有界修复：模型的选择必须被候选集、营养和禁忌规则约束。"""
from dataclasses import dataclass, field

from services.planning.candidates import MEAL_RATIOS
from services.planning.schema import MEAL_KEYS, PlanSelection

CALORIE_TOLERANCE = 0.05
MEAL_CALORIE_TOLERANCE = 0.40
PROTEIN_FLOOR = 0.80


@dataclass
class Verification:
    ok: bool
    target_cal: float
    total_cal: float
    calorie_error_pct: float
    protein_g: float
    target_protein: float
    issues: list = field(default_factory=list)
    invalid_ids: list = field(default_factory=list)
    danger_ids: list = field(default_factory=list)
    meal_totals: dict = field(default_factory=dict)
    items: dict = field(default_factory=dict)


def _candidate_map(candidates):
    return {
        meal: {c['recipe_id']: c for c in (candidates.get(meal) or [])}
        for meal in MEAL_KEYS
    }


def _target_protein(user):
    return max(60.0, float(user.current_weight or 60) * 1.2)


def evaluate_selection(selection, candidates, user):
    """按数据库候选的每100g营养重算，绝不相信模型自报数字。"""
    by_meal = _candidate_map(candidates)
    target_cal = float(user.recommend_cal or 1800)
    target_protein = _target_protein(user)
    issues, invalid_ids, danger_ids = [], [], []
    meal_totals, items = {}, {meal: [] for meal in MEAL_KEYS}
    total_cal = total_protein = 0.0

    for meal in MEAL_KEYS:
        meal_cal = meal_protein = 0.0
        for dish in getattr(selection, meal):
            candidate = by_meal[meal].get(dish.recipe_id)
            if candidate is None:
                invalid_ids.append(dish.recipe_id)
                issues.append(f'{meal}: recipe_id={dish.recipe_id} 不在候选集')
                continue
            if candidate.get('health_level') == 'danger':
                danger_ids.append(dish.recipe_id)
                issues.append(f'{meal}: recipe_id={dish.recipe_id} 触发禁忌')
                continue

            factor = dish.weight_g / 100.0
            cal = candidate['calorie_per_100g'] * factor
            protein = candidate['protein_per_100g'] * factor
            meal_cal += cal
            meal_protein += protein
            items[meal].append({
                'recipe_id': dish.recipe_id,
                'recipe_name': candidate['recipe_name'],
                'weight_g': dish.weight_g,
                'calorie': round(cal, 1),
                'protein_g': round(protein, 1),
                'fat_g': round(candidate['fat_g'] * dish.weight_g / (candidate['total_weight'] or 100), 1)
                if candidate['total_weight'] else 0,
                'carbohydrate_g': round(
                    candidate['carbohydrate_g'] * dish.weight_g / (candidate['total_weight'] or 100), 1
                ) if candidate['total_weight'] else 0,
                'health_level': candidate.get('health_level', 'ok'),
            })

        meal_totals[meal] = {'cal': round(meal_cal, 1), 'protein_g': round(meal_protein, 1)}
        total_cal += meal_cal
        total_protein += meal_protein

    for meal in ('breakfast', 'lunch', 'dinner'):
        if not items[meal]:
            issues.append(f'{meal}: 没有有效菜品')
            continue
        meal_target = target_cal * MEAL_RATIOS[meal]
        meal_error = abs(meal_totals[meal]['cal'] - meal_target) / meal_target
        if meal_error > MEAL_CALORIE_TOLERANCE:
            issues.append(
                f'{meal}: 热量 {meal_totals[meal]["cal"]:.0f} 偏离该餐目标 '
                f'{meal_target:.0f} 超过 ±40%'
            )
    if not any(items.values()):
        issues.append('没有选中任何有效菜品')

    error_pct = abs(total_cal - target_cal) / target_cal * 100 if target_cal else 0.0
    if error_pct > CALORIE_TOLERANCE * 100:
        issues.append(f'总热量偏差 {error_pct:.1f}% 超过 ±5%')
    if total_protein < target_protein * PROTEIN_FLOOR:
        issues.append(
            f'蛋白质 {total_protein:.1f}g 低于目标 {target_protein:.1f}g 的 80%'
        )

    return Verification(
        ok=not issues,
        target_cal=target_cal,
        total_cal=round(total_cal, 1),
        calorie_error_pct=round(error_pct, 1),
        protein_g=round(total_protein, 1),
        target_protein=round(target_protein, 1),
        issues=issues,
        invalid_ids=invalid_ids,
        danger_ids=danger_ids,
        meal_totals=meal_totals,
        items=items,
    )


def _best_candidate(candidates, meal, target_cal, used_ids):
    available = [
        c for c in (candidates.get(meal) or [])
        if c['recipe_id'] not in used_ids and c.get('health_level') != 'danger'
    ]
    if not available:
        return None
    return min(available, key=lambda c: abs(c['total_calorie'] - target_cal))


def _weight_for(candidate, target_cal):
    per100 = candidate['calorie_per_100g'] or 1
    return max(30.0, min(600.0, round(target_cal / per100 * 100, 1)))


def repair_selection(selection, candidates, verification, user):
    """确定性修复：删非法/危险项 → 补空主餐 → 缩放热量 → 必要时去掉加餐。"""
    target_total = float(user.recommend_cal or 1800)
    by_meal = _candidate_map(candidates)
    used_ids = set()
    repaired = 0
    plan = {meal: [] for meal in MEAL_KEYS}
    plan['tips'] = selection.tips

    for meal in MEAL_KEYS:
        for dish in getattr(selection, meal):
            candidate = by_meal[meal].get(dish.recipe_id)
            if candidate is None or candidate.get('health_level') == 'danger':
                repaired += 1
                continue
            if dish.recipe_id in used_ids:
                repaired += 1
                continue
            plan[meal].append({'recipe_id': dish.recipe_id, 'weight_g': dish.weight_g})
            used_ids.add(dish.recipe_id)

        if meal in ('breakfast', 'lunch', 'dinner') and not plan[meal]:
            target = target_total * MEAL_RATIOS[meal]
            candidate = _best_candidate(candidates, meal, target, used_ids)
            if candidate:
                plan[meal].append({
                    'recipe_id': candidate['recipe_id'],
                    'weight_g': _weight_for(candidate, target),
                })
                used_ids.add(candidate['recipe_id'])
                repaired += 1

    normalized = PlanSelection.model_validate(plan)
    current = evaluate_selection(normalized, candidates, user)

    # 先按每餐目标做一次再平衡，避免“总热量对了但午餐爆表”
    if current.total_cal > 0:
        for meal in ('breakfast', 'lunch', 'dinner'):
            meal_target = target_total * MEAL_RATIOS[meal]
            meal_cal = current.meal_totals[meal]['cal']
            if meal_cal <= 0:
                continue
            meal_factor = max(0.6, min(1.6, meal_target / meal_cal))
            if abs(meal_factor - 1.0) > 0.001:
                for dish in getattr(normalized, meal):
                    dish.weight_g = max(30.0, min(600.0, round(dish.weight_g * meal_factor, 1)))
                repaired += 1
        current = evaluate_selection(normalized, candidates, user)

    if current.total_cal > 0:
        factor = max(0.5, min(2.5, target_total / current.total_cal))
        if abs(factor - 1.0) > 0.001:
            for meal in MEAL_KEYS:
                for dish in getattr(normalized, meal):
                    dish.weight_g = max(30.0, min(600.0, round(dish.weight_g * factor, 1)))
            repaired += 1

    current = evaluate_selection(normalized, candidates, user)
    # 仍然超标且是加餐造成的，直接去掉加餐再缩放一次
    if current.total_cal > target_total * (1 + CALORIE_TOLERANCE) and normalized.snack:
        normalized = PlanSelection.model_validate({
            **normalized.model_dump(exclude={'snack'}),
            'snack': [],
        })
        current = evaluate_selection(normalized, candidates, user)
        if current.total_cal > 0:
            factor = max(0.5, min(1.0, target_total / current.total_cal))
            for meal in MEAL_KEYS:
                for dish in getattr(normalized, meal):
                    dish.weight_g = max(30.0, min(600.0, round(dish.weight_g * factor, 1)))
        repaired += 1

    return normalized, repaired
