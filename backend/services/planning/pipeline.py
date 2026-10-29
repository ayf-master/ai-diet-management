"""可信规划编排：候选 → 闭集选择 → 校验 → 修复 → 再生成一次 → 落库指标。"""
import time
from dataclasses import dataclass, field

from pydantic import ValidationError

from models import Recipe
from services.errors import DomainError
from services.health_check import load_user_disease_rules
from services.planning.candidates import MEAL_RATIOS, candidate_count, recall_candidates
from services.planning.llm import generate_selection
from services.planning.schema import MEAL_KEYS, PlanSelection
from services.planning.verification import evaluate_selection, repair_selection


@dataclass
class PlanResult:
    plan: dict
    selection: PlanSelection
    verification: object
    metrics: dict
    source: str = 'model'
    model: str = ''
    attempts: int = 1
    warnings: list = field(default_factory=list)


def _empty_selection():
    return PlanSelection.model_validate({meal: [] for meal in MEAL_KEYS})


def _fallback_selection(candidates, user):
    total_target = float(user.recommend_cal or 1800)
    plan = {meal: [] for meal in MEAL_KEYS}
    plan['tips'] = '（数据库兜底选择）本方案由候选集自动组合，建议配置模型后重新生成。'
    used = set()
    for meal in MEAL_KEYS:
        items = [
            c for c in (candidates.get(meal) or [])
            if c['recipe_id'] not in used and c.get('health_level') != 'danger'
        ]
        if not items:
            continue
        target = total_target * MEAL_RATIOS[meal]
        chosen = min(items, key=lambda c: abs(c['total_calorie'] - target))
        per100 = chosen['calorie_per_100g'] or 1
        weight = max(30.0, min(600.0, round(target / per100 * 100, 1)))
        plan[meal].append({'recipe_id': chosen['recipe_id'], 'weight_g': weight})
        used.add(chosen['recipe_id'])
    return PlanSelection.model_validate(plan)


def _enrich(selection, verification, candidates):
    selected_ids = [
        dish.recipe_id for meal in MEAL_KEYS for dish in getattr(selection, meal)
    ]
    recipes = {
        r.recipe_id: r
        for r in Recipe.query.filter(Recipe.recipe_id.in_(selected_ids)).all()
    } if selected_ids else {}

    plan = {meal: [] for meal in MEAL_KEYS}
    for meal in MEAL_KEYS:
        for item in verification.items.get(meal, []):
            recipe = recipes.get(item['recipe_id'])
            foods = []
            if recipe:
                total_weight = recipe.total_weight or 100
                for rf in recipe.ingredients:
                    foods.append({
                        'food': rf.food.food_name if rf.food else '',
                        'weight_g': round((rf.weight or 0) * item['weight_g'] / total_weight, 1),
                    })
            plan[meal].append({
                **item,
                'dish': item['recipe_name'],
                'foods': foods,
            })

    plan['total_cal'] = round(verification.total_cal)
    plan['protein_g'] = verification.protein_g
    plan['tips'] = selection.tips or ''
    plan['verification'] = {
        'ok': verification.ok,
        'calorie_error_pct': verification.calorie_error_pct,
        'target_cal': verification.target_cal,
        'protein_g': verification.protein_g,
        'target_protein': verification.target_protein,
        'issues': verification.issues,
    }
    return plan


def _metrics(verification, source, model, attempts, parsed, schema_ok,
             repair_count, candidate_total, started, fallback_used,
             invalid_count, danger_count):
    return {
        'status': (
            'fallback' if fallback_used
            else ('ok' if verification.ok and repair_count == 0 else 'repaired')
        ),
        'model': model,
        'source': source,
        'candidate_count': candidate_total,
        'attempts': attempts,
        'parse_ok': bool(parsed),
        'schema_ok': bool(schema_ok),
        'invalid_id_count': invalid_count,
        'repaired_count': repair_count,
        'danger_count': danger_count,
        'target_cal': round(verification.target_cal),
        'verified_cal': round(verification.total_cal),
        'calorie_error_pct': verification.calorie_error_pct,
        'protein_g': verification.protein_g,
        'fallback_used': fallback_used,
        'latency_ms': round((time.perf_counter() - started) * 1000),
    }


def generate_trusted_plan(user, diseases=None, selection_provider=None):
    """返回 PlanResult；调用方负责 plan/run 的数据库事务。"""
    started = time.perf_counter()
    provider = selection_provider or generate_selection
    rules = load_user_disease_rules(user.user_id)
    candidates = recall_candidates(user, rules)
    total_candidates = candidate_count(candidates)
    if total_candidates == 0:
        raise DomainError(503, '没有可用的食谱候选，请先补充系统食谱')

    selection = _empty_selection()
    verification = evaluate_selection(selection, candidates, user)
    source, model = 'model', ''
    attempts = 0
    parsed = False
    schema_ok = False
    repair_count = 0
    correction = None
    fallback_used = False
    invalid_count = 0
    danger_count = 0

    while attempts < 2:
        attempts += 1
        try:
            result = provider(user.to_dict(), diseases or [], candidates, correction)
            source = result.get('source', 'model')
            model = result.get('model', '')
            raw = result.get('plan_data')
            parsed = isinstance(raw, dict)
            if parsed:
                try:
                    selection = PlanSelection.model_validate(raw)
                    schema_ok = True
                except ValidationError as exc:
                    correction = str(exc.errors()[:3])
                    schema_ok = False
                    selection = _empty_selection()
            else:
                correction = '输出无法解析为 JSON；只输出规定字段。'
        except Exception as exc:  # 模型/网络异常也只降级，不把脏数据写库
            correction = f'上次调用失败：{str(exc)[:200]}'
            parsed, schema_ok = False, False
            selection = _empty_selection()

        # schema 不合法时先给模型一次修正机会；不要在第一次坏 JSON 后直接兜底
        if not schema_ok and attempts < 2:
            if not correction:
                correction = '输出不符合 schema；只输出 recipe_id 与 weight_g。'
            continue

        verification = evaluate_selection(selection, candidates, user)
        invalid_count = max(invalid_count, len(verification.invalid_ids))
        danger_count = max(danger_count, len(verification.danger_ids))
        if not verification.ok:
            selection, repaired = repair_selection(selection, candidates, verification, user)
            repair_count += repaired
            verification = evaluate_selection(selection, candidates, user)
        if verification.ok:
            break

        if attempts < 2:
            correction = '；'.join(verification.issues[:8])

    if not verification.ok:
        fallback_used = True
        source = 'fallback'
        selection = _fallback_selection(candidates, user)
        selection, repaired = repair_selection(selection, candidates, verification, user)
        repair_count += repaired
        verification = evaluate_selection(selection, candidates, user)

    plan = _enrich(selection, verification, candidates)
    metrics = _metrics(
        verification, source, model, attempts, parsed, schema_ok,
        repair_count, total_candidates, started, fallback_used,
        invalid_count, danger_count,
    )
    warnings = []
    if not verification.ok:
        warnings.append('最终方案仍未通过全部校验，请人工复核')
    return PlanResult(
        plan=plan,
        selection=selection,
        verification=verification,
        metrics=metrics,
        source=source,
        model=model,
        attempts=attempts,
        warnings=warnings,
    )
