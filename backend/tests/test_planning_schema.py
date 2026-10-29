"""闭集输出 schema：只允许 recipe_id + weight_g。"""
import pytest
from pydantic import ValidationError

from services.planning.schema import PlanSelection


def test_valid_selection():
    selection = PlanSelection.model_validate({
        'breakfast': [{'recipe_id': 4, 'weight_g': 180}],
        'lunch': [{'recipe_id': 1, 'weight_g': 300}],
        'dinner': [],
        'snack': [],
        'tips': '少油',
    })
    assert selection.breakfast[0].recipe_id == 4
    assert selection.lunch[0].weight_g == 300


def test_rejects_model_reported_calories():
    with pytest.raises(ValidationError):
        PlanSelection.model_validate({
            'breakfast': [{'recipe_id': 4, 'weight_g': 180, 'total_cal': 999}],
        })


def test_rejects_unknown_meal_and_bad_weight():
    with pytest.raises(ValidationError):
        PlanSelection.model_validate({'brunch': [{'recipe_id': 4, 'weight_g': 180}]})
    with pytest.raises(ValidationError):
        PlanSelection.model_validate({
            'breakfast': [{'recipe_id': 4, 'weight_g': 5}],
        })
