
"""闭集选择 prompt 与调用；模型只返回 recipe_id + weight_g。"""
import json



from services.ai_service import _get_client, _repair_json_text, format_taboo_prompt
from services.planning.candidates import MEAL_RATIOS


_MEAL_TITLES = {
    'breakfast': '早餐',
    'lunch': '午餐',
    'dinner': '晚餐',
    'snack': '加餐',
}


def _format_candidates(candidates):
    lines = []
    for meal_key in ('breakfast', 'lunch', 'dinner', 'snack'):
        lines.append(f'【{_MEAL_TITLES[meal_key]}】')
        items = candidates.get(meal_key) or []
        if not items:
            lines.append('- （本餐暂无候选，必须返回空数组）')
            continue
        for c in items:
            warn = ''
            if c.get('health_level') == 'warn':
                warn = '；注意：' + '；'.join(c.get('health_reasons') or [])
            lines.append(
                f"- id={c['recipe_id']} {c['recipe_name']} "
                f"{c['total_calorie']:.0f}kcal/{c['total_weight']:.0f}g "
                f"蛋白{c['protein_g']:.1f}g 适合{c['suitable_goals']}{warn}"
            )
    return '\n'.join(lines)


def _prompt(user_info, diseases, candidates, correction=None):
    goal_map = {'lose_weight': '减脂', 'gain_muscle': '增肌', 'healthy': '健康饮食'}
    goal = goal_map.get(user_info.get('diet_goal'), '健康饮食')
    forbid = ''
    if diseases:
        forbid = (
            '\n【饮食禁忌】只能选不触发以下禁忌的候选：\n'
            f'{format_taboo_prompt(diseases)}'
        )
    fix = ''
    if correction:
        fix = f'\n【上次输出问题，必须修正】\n{correction}'

    return f'''你是一个饮食规划器。你只能从下面数据库候选表中选菜，禁止编造菜名或食材。

【用户】
- 目标：{goal}
- 推荐日摄入：{user_info.get('recommend_cal')}kcal
- 当前体重：{user_info.get('current_weight')}kg，身高：{user_info.get('height')}cm
{forbid}

【候选表】
{_format_candidates(candidates)}

【输出要求】
只输出一个 JSON 对象，且只能包含这些字段：
{{
  "breakfast": [{{"recipe_id": 整数, "weight_g": 数字}}],
  "lunch": [{{"recipe_id": 整数, "weight_g": 数字}}],
  "dinner": [{{"recipe_id": 整数, "weight_g": 数字}}],
  "snack": [{{"recipe_id": 整数, "weight_g": 数字}}],
  "tips": "不超过100字的建议"
}}
规则：
1. 每个 recipe_id 必须来自对应餐次的候选表；不能跨餐次选。
2. weight_g 在 30–600 之间；早餐/午餐/晚餐至少各选 1 道；加餐可为空。
3. 总热量尽量接近推荐日摄入；不要输出热量、蛋白质、菜名或其他字段。
4. 只输出 JSON，不要 markdown，不要解释。{fix}'''


def _mock_selection(user_info, candidates):
    """无模型密钥时的确定性选择：每个有候选的餐次选热量最接近目标的一道。"""
    total_target = float(user_info.get('recommend_cal') or 1800)
    plan = {'breakfast': [], 'lunch': [], 'dinner': [], 'snack': [], 'tips': '（演示选择）请配置模型密钥以获得更丰富的搭配。'}
    for meal_key in ('breakfast', 'lunch', 'dinner', 'snack'):
        items = candidates.get(meal_key) or []
        if not items:
            continue
        target = total_target * MEAL_RATIOS[meal_key]
        chosen = min(items, key=lambda c: abs(c['total_calorie'] - target))
        per100 = chosen['calorie_per_100g'] or 1
        weight = max(30, min(600, round(target / per100 * 100, 1)))
        plan[meal_key].append({'recipe_id': chosen['recipe_id'], 'weight_g': weight})
    return plan


def generate_selection(user_info, diseases, candidates, correction=None):
    client = _get_client()
    if client is None:
        plan = _mock_selection(user_info, candidates)
        return {
            'raw_text': json.dumps(plan, ensure_ascii=False),
            'plan_data': plan,
            'source': 'mock',
            'model': 'mock',
        }

    response = client.chat.completions.create(
        model=AI_MODEL,
        messages=[
            {'role': 'system', 'content': _prompt(user_info, diseases, candidates, correction)},
            {'role': 'user', 'content': '请从候选表中选择并给出克数。'},
        ],
        temperature=0.2,
        max_tokens=1200,
    )
    content = response.choices[0].message.content or ''
    raw = content.strip()
    if raw.startswith('```json'):
        raw = raw[7:]
    elif raw.startswith('```'):
        raw = raw[3:]
    if raw.endswith('```'):
        raw = raw[:-3]
    raw = raw.strip()

    return {
        'raw_text': content,
        'plan_data': _repair_json_text(raw),
        'source': 'model',
        'model': AI_MODEL,
    }
