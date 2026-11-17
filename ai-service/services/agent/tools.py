"""Agent 工具层（阶段 7.1）：只读工具 + 注册表 + 统一执行/失败结构。

模型只输出“调用意图”，本层负责参数校验、身份注入、可见性校验和执行。
"""
import logging
from dataclasses import dataclass
from typing import Any, Callable, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from sqlalchemy import or_, text

from db import db
from models import Recipe
from services.health_check import load_user_diseases, load_user_disease_rules
from services.planning.candidates import recall_meal_candidates

logger = logging.getLogger(__name__)

IDENTITY_FIELDS = {'user_id', 'owner_id', 'admin_id'}


@dataclass
class ToolResult:
    ok: bool
    data: Any = None
    error_code: str | None = None
    message: str = ''

    def to_dict(self):
        return {
            'ok': self.ok,
            'data': self.data,
            'error_code': self.error_code,
            'message': self.message,
        }


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    args_model: type[BaseModel]
    handler: Callable[[BaseModel, Any], ToolResult]
    read_only: bool = True


def _strip_schema_titles(node):
    """Pydantic 会塞很多 title，模型不需要；递归清掉，保持 schema 紧凑。"""
    if isinstance(node, dict):
        node.pop('title', None)
        for value in node.values():
            _strip_schema_titles(value)
    elif isinstance(node, list):
        for item in node:
            _strip_schema_titles(item)


def to_openai_tool(spec: ToolSpec) -> dict:
    """把 ToolSpec 转成 OpenAI/DeepSeek function calling 的 tool schema。"""
    parameters = spec.args_model.model_json_schema()
    _strip_schema_titles(parameters)
    parameters['additionalProperties'] = False

    return {
        'type': 'function',
        'function': {
            'name': spec.name,
            'description': spec.description,
            'parameters': parameters,
        },
    }


class ToolRegistry:
    """严格 allowlist：模型只能调用注册过的工具。"""

    def __init__(self):
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec):
        if spec.name in self._tools:
            raise ValueError(f'tool already registered: {spec.name}')
        self._tools[spec.name] = spec

    def get(self, name):
        return self._tools.get(name)

    def names(self):
        return sorted(self._tools)

    def specs(self):
        return [self._tools[name] for name in self.names()]

    def execute(self, name, raw_args, current_user):
        spec = self._tools.get(name)
        if spec is None:
            return ToolResult(
                ok=False,
                error_code='unknown_tool',
                message=f'未知工具：{name}',
            )

        if raw_args is None:
            raw_args = {}
        if not isinstance(raw_args, dict):
            return ToolResult(
                ok=False,
                error_code='invalid_arguments',
                message='工具参数必须是 JSON 对象',
            )

        # 身份字段一律由登录态注入；模型传了就拒绝，避免它尝试指定别人
        if IDENTITY_FIELDS & set(raw_args):
            return ToolResult(
                ok=False,
                error_code='invalid_arguments',
                message='user_id/owner_id/admin_id 由服务端注入，不能由模型传入',
            )

        try:
            args = spec.args_model.model_validate(raw_args)
        except ValidationError as exc:
            detail = '; '.join(
                f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}"
                for e in exc.errors()[:3]
            )
            return ToolResult(
                ok=False,
                error_code='invalid_arguments',
                message=detail,
            )

        try:
            result = spec.handler(args, current_user)
        except Exception as exc:
            logger.exception('tool failed: %s', name)
            return ToolResult(
                ok=False,
                error_code='tool_failed',
                message=f'工具执行失败：{type(exc).__name__}',
            )

        if isinstance(result, ToolResult):
            return result
        return ToolResult(ok=True, data=result)


class UserProfileArgs(BaseModel):
    model_config = ConfigDict(extra='forbid')


class SearchRecipesArgs(BaseModel):
    model_config = ConfigDict(extra='forbid')

    meal_type: Literal['breakfast', 'lunch', 'dinner', 'snack'] = Field(
        ...,
        description='餐次：breakfast=早餐，lunch=午餐，dinner=晚餐，snack=加餐',
    )
    goal: Literal['lose_weight', 'gain_muscle', 'healthy'] = Field(
        default='healthy',
        description='饮食目标：减脂、增肌或健康饮食',
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=8,
        description='最多返回几个候选，默认 5',
    )


class CalculateNutritionArgs(BaseModel):
    model_config = ConfigDict(extra='forbid')

    recipe_id: int = Field(
        default=0,
        ge=0,
        description='食谱 ID；与 recipe_name 二选一',
    )
    recipe_name: str = Field(
        default='',
        max_length=50,
        description='食谱名称；与 recipe_id 二选一，适合只知道菜名时使用',
    )
    weight_g: float = Field(ge=30, le=600, description='实际食用克数，范围 30–600')

    @model_validator(mode='after')
    def exactly_one_identifier(self):
        self.recipe_name = self.recipe_name.strip()
        if bool(self.recipe_id) == bool(self.recipe_name):
            raise ValueError('recipe_id 和 recipe_name 必须且只能提供一个')
        return self


def _get_profile(args, user):
    diseases = load_user_diseases(user.user_id)
    return ToolResult(ok=True, data={
        'user_id': user.user_id,
        'diet_goal': user.diet_goal,
        'recommend_cal': user.recommend_cal,
        'current_weight': user.current_weight,
        'target_weight': user.target_weight,
        'height': user.height,
        'bmi': user.bmi,
        'diseases': [d.disease_name for d in diseases],
    })


def _search_recipes(args, user):
    rules = load_user_disease_rules(user.user_id)
    items = recall_meal_candidates(
        user, args.meal_type, disease_rules=rules, goal=args.goal, limit=args.limit,
    )
    candidates = [{
        'recipe_id': c['recipe_id'],
        'recipe_name': c['recipe_name'],
        'type': c['type'],
        'suitable_goals': c['suitable_goals'],
        'total_weight': c['total_weight'],
        'total_calorie': c['total_calorie'],
        'protein_g': c['protein_g'],
        'calorie_per_100g': c['calorie_per_100g'],
        'health_level': c['health_level'],
    } for c in items]
    return ToolResult(ok=True, data={
        'meal_type': args.meal_type,
        'goal': args.goal,
        'count': len(candidates),
        'candidates': candidates,
    })


def _calculate_nutrition(args, user):
    if args.recipe_id:
        recipe = db.session.get(Recipe, args.recipe_id)
        if recipe is None or recipe.user_id not in (None, user.user_id):
            return ToolResult(
                ok=False,
                error_code='not_found',
                message='食谱不存在或当前用户不可见',
            )
    else:
        visible = or_(Recipe.user_id.is_(None), Recipe.user_id == user.user_id)
        matches = Recipe.query.filter(
            Recipe.recipe_name == args.recipe_name,
            visible,
        ).all()
        if not matches:
            matches = Recipe.query.filter(
                Recipe.recipe_name.contains(args.recipe_name),
                visible,
            ).limit(5).all()
        if not matches:
            return ToolResult(
                ok=False,
                error_code='not_found',
                message=f'没有找到名为“{args.recipe_name}”的可见食谱',
            )
        if len(matches) > 1:
            own = [r for r in matches if r.user_id == user.user_id]
            if len(own) == 1:
                recipe = own[0]
            else:
                names = '、'.join(r.recipe_name for r in matches[:5])
                return ToolResult(
                    ok=False,
                    error_code='not_found',
                    message=f'找到多个同名或相近食谱：{names}，请改用 recipe_id',
                )
        else:
            recipe = matches[0]

    row = db.session.execute(
        text("""
            SELECT recipe_name, total_weight, calorie_per_100g,
                   protein_per_100g, fat_g, carbohydrate_g
            FROM v_recipe_nutrition
            WHERE recipe_id = :recipe_id
        """),
        {'recipe_id': recipe.recipe_id},
    ).mappings().first()
    if row is None:
        return ToolResult(
            ok=False,
            error_code='not_found',
            message='食谱营养数据不存在',
        )

    factor = args.weight_g / 100.0
    total_weight = float(row['total_weight'] or 0)
    fat_scale = args.weight_g / total_weight if total_weight else 0
    return ToolResult(ok=True, data={
        'recipe_id': recipe.recipe_id,
        'recipe_name': row['recipe_name'],
        'weight_g': args.weight_g,
        'calorie': round(float(row['calorie_per_100g'] or 0) * factor, 1),
        'protein_g': round(float(row['protein_per_100g'] or 0) * factor, 1),
        'fat_g': round(float(row['fat_g'] or 0) * fat_scale, 1),
        'carbohydrate_g': round(float(row['carbohydrate_g'] or 0) * fat_scale, 1),
    })


def build_registry():
    registry = ToolRegistry()
    registry.register(ToolSpec(
        name='get_user_profile',
        description='读取当前登录用户的目标、推荐热量、体重、BMI 和疾病名称；无参数。',
        args_model=UserProfileArgs,
        handler=_get_profile,
        read_only=True,
    ))
    registry.register(ToolSpec(
        name='search_recipes',
        description='按餐次和目标召回当前用户可见的食谱候选，返回营养摘要。',
        args_model=SearchRecipesArgs,
        handler=_search_recipes,
        read_only=True,
    ))
    registry.register(ToolSpec(
        name='calculate_recipe_nutrition',
        description='按 recipe_id 或 recipe_name + 克数，用数据库营养视图重算一道可见食谱的热量和宏量营养。',
        args_model=CalculateNutritionArgs,
        handler=_calculate_nutrition,
        read_only=True,
    ))
    return registry


TOOL_REGISTRY = build_registry()


def execute_tool(name, raw_args, current_user):
    return TOOL_REGISTRY.execute(name, raw_args, current_user)
