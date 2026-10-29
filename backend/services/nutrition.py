"""纯营养计算：不依赖 Flask、不查数据库，方便单测与复用。

公式来源（与改造前路由内逻辑保持一致）：
- 生食材热量 = Σ(每 100g 热量 × 克数 / 100)
- 油 9 kcal/g，酱 4 kcal/g
- 没有显式油/酱克数时，用烹饪方式的「每 100g 油/酱热量」× 总重量 / 100
- total 用未四舍五入的 base 计算，避免与旧实现的 ±1 kcal 偏差
"""
from dataclasses import dataclass

OIL_KCAL_PER_G = 9.0
SAUCE_KCAL_PER_G = 4.0


@dataclass(frozen=True)
class IngredientNutrition:
    """一个食材对计算的输入：克数 + 每 100g 热量（可为空，表示库里没营养数据）。"""

    weight: float
    calorie_per_100g: float | None = None


@dataclass(frozen=True)
class RecipeTotals:
    total_weight: float
    base_calorie: int
    added_calorie: int
    total_calorie: int


@dataclass(frozen=True)
class MealItemTotals:
    oil_g: float
    sauce_g: float
    single_cal: int


def _as_float(value, default=0.0):
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def added_calories_from_grams(oil_g=0, sauce_g=0):
    """用户直接填写油/酱绝对克数时的附加热量。"""
    return round(
        _as_float(oil_g) * OIL_KCAL_PER_G
        + _as_float(sauce_g) * SAUCE_KCAL_PER_G
    )


def added_calories_from_cook_method_raw(
    total_weight, oil_per_100g=0, sauce_kcal_per_100g=0
):
    """按烹饪方式系数算附加热量，返回未取整值（供展示层保留旧的四舍五入行为）。"""
    weight = _as_float(total_weight)
    if weight <= 0:
        return 0.0
    oil = _as_float(oil_per_100g) * weight / 100.0 * OIL_KCAL_PER_G
    sauce = _as_float(sauce_kcal_per_100g) * weight / 100.0
    return oil + sauce


def calc_recipe_totals(
    ingredients,
    *,
    oil_g=0,
    sauce_g=0,
    oil_per_100g=0,
    sauce_kcal_per_100g=0,
):
    """根据食材与烹饪参数计算食谱总重量/基础热量/附加热量/总热量。"""
    total_weight = 0.0
    base_raw = 0.0
    for ingredient in ingredients:
        weight = _as_float(ingredient.weight)
        total_weight += weight
        calorie = _as_float(ingredient.calorie_per_100g)
        if calorie:
            base_raw += calorie * weight / 100.0

    # 显式油/酱克数优先；否则回退烹饪方式系数，和旧实现一致
    if _as_float(oil_g) or _as_float(sauce_g):
        added_calorie = added_calories_from_grams(oil_g, sauce_g)
    else:
        added_calorie = round(
            added_calories_from_cook_method_raw(
                total_weight, oil_per_100g, sauce_kcal_per_100g
            )
        )

    return RecipeTotals(
        total_weight=total_weight,
        base_calorie=round(base_raw),
        added_calorie=added_calorie,
        total_calorie=round(base_raw + added_calorie),
    )


def calc_meal_item(
    recipe_total_weight,
    recipe_base_calorie,
    recipe_total_calorie,
    recipe_oil_g,
    recipe_sauce_g,
    eat_weight,
    *,
    override_oil=None,
    override_sauce=None,
):
    """打卡单条明细：按份量缩放食谱热量，支持当天油/酱覆盖。

    保留旧实现的优先级：
    1. 同时填写 oil_g/sauce_g 且至少一个非 0 → 用覆盖值；
    2. 否则食谱自带油/酱 → 按份量比缩放；
    3. 否则用食谱总热量整体缩放。
    """
    weight = _as_float(eat_weight)
    r_weight = _as_float(recipe_total_weight)
    r_oil = _as_float(recipe_oil_g)
    r_sauce = _as_float(recipe_sauce_g)

    override_oil = None if override_oil is None else _as_float(override_oil)
    override_sauce = None if override_sauce is None else _as_float(override_sauce)
    has_override = override_oil is not None and override_sauce is not None
    override_used = has_override and bool(override_oil or override_sauce)

    if override_used:
        oil_g, sauce_g = override_oil, override_sauce
    elif r_oil or r_sauce:
        scale = weight / (r_weight or weight or 1)
        oil_g, sauce_g = r_oil * scale, r_sauce * scale
    else:
        oil_g = sauce_g = 0.0

    base_part = _as_float(recipe_base_calorie) * weight / (r_weight or 100)
    if override_used or r_oil or r_sauce:
        single_cal = round(base_part + oil_g * OIL_KCAL_PER_G + sauce_g * SAUCE_KCAL_PER_G)
    else:
        single_cal = round(_as_float(recipe_total_calorie) * weight / (r_weight or 100))

    return MealItemTotals(
        oil_g=round(oil_g, 2),
        sauce_g=round(sauce_g, 2),
        single_cal=single_cal,
    )
