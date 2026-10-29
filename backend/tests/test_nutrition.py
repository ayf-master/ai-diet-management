"""纯营养计算单测：不连数据库、不起 Flask。"""
from services import nutrition


def test_added_calories_from_explicit_grams():
    # 10g 油 + 5g 酱 = 90 + 20
    assert nutrition.added_calories_from_grams(10, 5) == 110
    assert nutrition.added_calories_from_grams(0, 0) == 0
    assert nutrition.added_calories_from_grams(10, None) == 90


def test_totals_with_explicit_oil_and_sauce():
    totals = nutrition.calc_recipe_totals(
        [
            nutrition.IngredientNutrition(100, 133),
            nutrition.IngredientNutrition(50, 389),
        ],
        oil_g=10,
        sauce_g=5,
    )
    assert totals.total_weight == 150
    assert totals.base_calorie == 328          # 327.5 → 328
    assert totals.added_calorie == 110
    assert totals.total_calorie == 438         # 437.5 → 438


def test_totals_fall_back_to_cook_method_coefficients():
    totals = nutrition.calc_recipe_totals(
        [
            nutrition.IngredientNutrition(100, 133),
            nutrition.IngredientNutrition(50, 389),
        ],
        oil_per_100g=5,
        sauce_kcal_per_100g=10,
    )
    # 7.5g 油 ×9 + 15kcal 酱 = 82.5 → 82
    assert totals.added_calorie == 82
    assert totals.total_calorie == 410         # 327.5 + 82.5 = 410


def test_explicit_grams_take_precedence_over_cook_method():
    totals = nutrition.calc_recipe_totals(
        [nutrition.IngredientNutrition(100, 133)],
        oil_g=1,
        sauce_g=0,
        oil_per_100g=50,
        sauce_kcal_per_100g=100,
    )
    assert totals.added_calorie == 9           # 只认 1g 油
    assert totals.total_calorie == 142


def test_total_uses_unrounded_base_to_keep_legacy_behavior():
    # 50g×133/100 = 66.5；base 存 66，但 total 仍按 66.5+9=75.5 → 76
    totals = nutrition.calc_recipe_totals(
        [nutrition.IngredientNutrition(50, 133)],
        oil_g=1,
    )
    assert totals.base_calorie == 66
    assert totals.total_calorie == 76


def test_missing_nutrition_is_treated_as_zero():
    totals = nutrition.calc_recipe_totals(
        [
            nutrition.IngredientNutrition(100, None),
            nutrition.IngredientNutrition(50, 0),
        ],
        oil_per_100g=5,
    )
    assert totals.total_weight == 150
    assert totals.base_calorie == 0
    assert totals.total_calorie == 68          # 只有烹饪方式带来的 7.5g 油


# ---------- 打卡明细 ----------

def test_meal_without_explicit_oil_scales_total_calorie():
    item = nutrition.calc_meal_item(
        recipe_total_weight=100,
        recipe_base_calorie=133,
        recipe_total_calorie=133,
        recipe_oil_g=0,
        recipe_sauce_g=0,
        eat_weight=50,
    )
    assert item.oil_g == 0
    assert item.sauce_g == 0
    assert item.single_cal == 66               # round(66.5)，保留 Python 取整


def test_meal_with_recipe_oil_scales_by_weight():
    item = nutrition.calc_meal_item(
        recipe_total_weight=100,
        recipe_base_calorie=133,
        recipe_total_calorie=178,
        recipe_oil_g=5,
        recipe_sauce_g=0,
        eat_weight=50,
    )
    assert item.oil_g == 2.5
    assert item.single_cal == 89               # 66.5 + 2.5g 油×9


def test_meal_override_oil_and_sauce():
    item = nutrition.calc_meal_item(
        recipe_total_weight=100,
        recipe_base_calorie=133,
        recipe_total_calorie=133,
        recipe_oil_g=5,
        recipe_sauce_g=0,
        eat_weight=100,
        override_oil=10,
        override_sauce=5,
    )
    assert item.oil_g == 10
    assert item.sauce_g == 5
    assert item.single_cal == 243              # 133 + 90 + 20


def test_meal_override_both_zero_falls_back_to_recipe_oil():
    item = nutrition.calc_meal_item(
        recipe_total_weight=100,
        recipe_base_calorie=133,
        recipe_total_calorie=178,
        recipe_oil_g=5,
        recipe_sauce_g=0,
        eat_weight=100,
        override_oil=0,
        override_sauce=0,
    )
    assert item.oil_g == 5
    assert item.single_cal == 178


def test_meal_cook_method_only_uses_total_calorie():
    item = nutrition.calc_meal_item(
        recipe_total_weight=100,
        recipe_base_calorie=133,
        recipe_total_calorie=178,
        recipe_oil_g=0,
        recipe_sauce_g=0,
        eat_weight=50,
    )
    assert item.single_cal == 89               # 178×0.5，而不是 base×0.5
