"""LLM 唯一被允许输出的结构：只选候选 recipe_id，并给克数。

禁止菜名、热量、食材、营养字段，避免模型自报数据进入数据库真值。
"""
from pydantic import BaseModel, ConfigDict, Field

MEAL_KEYS = ('breakfast', 'lunch', 'dinner', 'snack')


class DishSelection(BaseModel):
    model_config = ConfigDict(extra='forbid')

    recipe_id: int = Field(gt=0)
    weight_g: float = Field(ge=30, le=600)


class PlanSelection(BaseModel):
    model_config = ConfigDict(extra='forbid')

    breakfast: list[DishSelection] = Field(default_factory=list)
    lunch: list[DishSelection] = Field(default_factory=list)
    dinner: list[DishSelection] = Field(default_factory=list)
    snack: list[DishSelection] = Field(default_factory=list)
    tips: str | None = Field(default=None, max_length=500)
