"""校验与修复的纯逻辑测试：不连数据库、不调用模型。"""
from types import SimpleNamespace

from services.planning.schema import PlanSelection
from services.planning.verification import evaluate_selection, repair_selection


def _candidate(recipe_id, meal, cal_per_100=133, protein_per_100=20):
    return {
        'recipe_id': recipe_id,
        'recipe_name': f'候选{recipe_id}',
        'type': meal,
        'total_weight': 300,
        'total_calorie': cal_per_100 * 3,
        'protein_g': protein_per_100 * 3,
        'fat_g': 6,
        'carbohydrate_g': 9,
        'calorie_per_100g': cal_per_100,
        'protein_per_100g': protein_per_100,
        'health_level': 'ok',
        'health_reasons': [],
    }


def _candidates():
    return {
        'breakfast': [_candidate(1, '早餐')],
        'lunch': [_candidate(2, '午餐')],
        'dinner': [_candidate(3, '晚餐')],
        'snack': [_candidate(4, '加餐')],
    }


def _user():
    return SimpleNamespace(recommend_cal=1500, current_weight=60)


def _selection(**overrides):
    plan = {
        'breakfast': [{'recipe_id': 1, 'weight_g': 250}],
        'lunch': [{'recipe_id': 2, 'weight_g': 500}],
        'dinner': [{'recipe_id': 3, 'weight_g': 400}],
        'snack': [],
    }
    plan.update(overrides)
    return PlanSelection.model_validate(plan)


def test_valid_selection_passes_tolerance():
    verification = evaluate_selection(_selection(), _candidates(), _user())
    assert verification.ok
    assert verification.total_cal == 1529.5
    assert verification.calorie_error_pct <= 5


def test_invalid_id_and_empty_main_meal_fail():
    selection = _selection(
        breakfast=[{'recipe_id': 999, 'weight_g': 200}],
        lunch=[], dinner=[],
    )
    verification = evaluate_selection(selection, _candidates(), _user())
    assert not verification.ok
    assert verification.invalid_ids == [999]
    assert any('没有有效菜品' in issue for issue in verification.issues)


def test_danger_candidate_fails():
    candidates = _candidates()
    candidates['lunch'][0]['health_level'] = 'danger'
    verification = evaluate_selection(_selection(), candidates, _user())
    assert not verification.ok
    assert verification.danger_ids == [2]


def test_repair_fills_empty_meals_and_scales():
    selection = PlanSelection.model_validate({
        'breakfast': [], 'lunch': [], 'dinner': [], 'snack': [],
    })
    candidates = _candidates()
    verification = evaluate_selection(selection, candidates, _user())
    repaired, count = repair_selection(selection, candidates, verification, _user())
    final = evaluate_selection(repaired, candidates, _user())

    assert count >= 3
    assert all(getattr(repaired, meal) for meal in ('breakfast', 'lunch', 'dinner'))
    assert final.ok
    assert final.calorie_error_pct <= 5
