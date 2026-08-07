import json
import re
from flask import current_app
from openai import OpenAI


# 营养阈值键 → (中文标签, 单位)
_NUTRI_LIMIT_LABEL = {
    'max_sugar': ('糖', 'g'),
    'max_sodium': ('钠', 'mg'),
    'max_fat': ('脂肪', 'g'),
    'max_carbohydrate': ('碳水', 'g'),
}


def _format_one_taboo(disease):
    """单条疾病禁忌转成给 AI 的文本。"""
    name = disease.disease_name
    desc = disease.forbid_desc or ''
    extra = []
    if disease.forbid_keywords:
        extra.append(f'忌口食材/类别：{disease.forbid_keywords}')
    if disease.forbid_rules:
        try:
            rules = json.loads(disease.forbid_rules)
        except Exception:
            rules = {}
        limits = []
        for key, val in rules.items():
            label, unit = _NUTRI_LIMIT_LABEL.get(key, (key.replace('max_', ''), ''))
            limits.append(f'{label}≤{val}{unit}/100g')
        if limits:
            extra.append('营养上限（单一食材每100g）：' + '，'.join(limits))
    remark = getattr(disease, 'remark', None)
    if remark:
        extra.append(f'用户备注（个性化信息）：{remark}')
    head = f'{name}：{desc}' if desc else name
    return head + '；' + '；'.join(extra) if extra else head


def format_taboo_prompt(diseases):
    """生成禁忌说明文本，每条疾病一行。"""
    if not diseases:
        return ''
    return '\n'.join(f'- {_format_one_taboo(d)}' for d in diseases)


def _get_client():
    api_key = current_app.config.get('AI_API_KEY')
    if not api_key:
        return None
    return OpenAI(
        api_key=api_key,
        base_url=current_app.config['AI_API_URL'],
    )


def _mock_diet_plan(user_info):
    """AI 不可用时的方案兜底。"""
    rec = user_info.get('recommend_cal') or 1800
    plan_data = {
        'breakfast': [
            {'dish': '燕麦牛奶粥', 'foods': [{'food': '燕麦', 'weight_g': 50}, {'food': '牛奶', 'weight_g': 200}]},
            {'dish': '水煮蛋', 'foods': [{'food': '鸡蛋', 'weight_g': 50}]},
        ],
        'lunch': [
            {'dish': '糙米饭', 'foods': [{'food': '糙米', 'weight_g': 100}]},
            {'dish': '清蒸鸡胸肉', 'foods': [{'food': '鸡胸肉', 'weight_g': 120}, {'food': '西兰花', 'weight_g': 150}]},
        ],
        'dinner': [
            {'dish': '番茄豆腐汤', 'foods': [{'food': '番茄', 'weight_g': 100}, {'food': '豆腐', 'weight_g': 150}]},
            {'dish': '蒸红薯', 'foods': [{'food': '红薯', 'weight_g': 100}]},
        ],
        'snack': [
            {'dish': '水果酸奶', 'foods': [{'food': '苹果', 'weight_g': 150}, {'food': '原味酸奶', 'weight_g': 100}]},
        ],
        'total_cal': rec,
        'tips': '（演示方案）保持三餐规律，优先高蛋白、低精制碳水；本方案为 AI 不可用时的兜底数据，请在配置模型密钥后重新生成。',
    }
    return {
        'plan_content': json.dumps(plan_data, ensure_ascii=False),
        'plan_data': plan_data,
        'total_cal': rec,
    }


def _mock_weekly_report(user_info, weekly_stats, weight_records):
    """AI 不可用时的周报兜底。"""
    days_logged = sum(1 for d in weekly_stats.get('daily', []) if d.get('cal', 0) > 0)
    total = weekly_stats.get('total_cal', 0)
    avg = total // max(days_logged, 1)
    trend = ''
    if weight_records and len(weight_records) >= 2:
        diff = weight_records[0].weight - weight_records[-1].weight
        trend = f'，体重{"下降" if diff < 0 else "上升"}{abs(diff):.1f}kg'
    comment = (f'本周累计打卡 {days_logged} 天，周总摄入约 {total}kcal，日均约 {avg}kcal{trend}。'
               '（演示数据）整体饮食结构基本合理，注意控制精制碳水与添加糖。')
    suggest = '（演示建议）保持规律三餐，增加优质蛋白与蔬菜比例，减少油炸与高糖食物；每周固定时间称重以观察趋势。配置模型密钥后可获得更精准的 AI 评价。'
    return {'ai_comment': comment, 'suggest': suggest, 'score': 75}


def _repair_json_text(text):
    """补全 AI 返回的未加引号 JSON 键/值。"""
    cleaned = text.strip()
    if cleaned.startswith('```json'):
        cleaned = cleaned[7:]
    elif cleaned.startswith('```'):
        cleaned = cleaned[3:]
    if cleaned.endswith('```'):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    repaired = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', cleaned)  # 补全未加引号的键
    # 补全未加引号的字符串值（中文/字母标识符）
    repaired = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_]*|[\u4e00-\u9fa5]+)\s*(?=[,}\]])', r': "\1"', repaired)

    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        return None


def generate_diet_plan(user_info, diseases=None):
    gender_text = '男' if user_info.get('gender') == 1 else '女'
    goal_map = {'lose_weight': '减脂', 'gain_muscle': '增肌', 'healthy': '健康饮食'}
    activity_map = {1: '静坐', 2: '轻度活动', 3: '中度活动', 4: '重度活动'}
    goal = goal_map.get(user_info.get('diet_goal', 'healthy'), '健康饮食')

    forbid_text = ''
    if diseases:
        lines = format_taboo_prompt(diseases)
        forbid_text = (
            '\n【用户饮食禁忌】请严格规避以下疾病对应的食材与营养上限'
            '（营养上限指「单一食材每100g」的含量，超过则不建议选用）：\n'
            f'{lines}'
        )

    prompt = f'''你是一个专业的减脂饮食营养师。请根据用户的身体数据，为用户生成一日三餐+加餐的饮食方案。

【用户信息】
- 年龄：{user_info.get('age')}岁
- 性别：{gender_text}
- 身高：{user_info.get('height')}cm
- 当前体重：{user_info.get('current_weight')}kg
- 目标体重：{user_info.get('target_weight')}kg
- BMI：{user_info.get('bmi')}
- 基础代谢(BMR)：{user_info.get('bmr')}kcal
- 活动等级：{activity_map.get(user_info.get('activity_level', 1), '静坐')}
- 饮食目标：{goal}
- 推荐日摄入量：{user_info.get('recommend_cal')}kcal
{forbid_text}

【要求】
1. 饮食方案必须符合推荐日摄入量
2. 每餐由若干「菜品」组成，每个菜品给出菜名和对应的食材清单（含大致克数），不需要给出做法
3. 注意营养均衡，菜品要家常、可操作
4. 输出格式必须是JSON，包含以下字段：
   - breakfast: [{{"dish": "菜名", "foods": [{{"food": "食材名", "weight_g": 数量}}]}}]
   - lunch: [{{"dish": "菜名", "foods": [{{"food": "食材名", "weight_g": 数量}}]}}]
   - dinner: [{{"dish": "菜名", "foods": [{{"food": "食材名", "weight_g": 数量}}]}}]
   - snack: [{{"dish": "菜名", "foods": [{{"food": "食材名", "weight_g": 数量}}]}}]
   - total_cal: 总热量(整数)
   - tips: "给用户的饮食建议"
5. 只输出JSON，不要有其他文字'''

    client = _get_client()
    if client is None:
        current_app.logger.warning('AI_API_KEY 未配置，使用演示方案兜底')
        return _mock_diet_plan(user_info)
    try:
        response = client.chat.completions.create(
            model=current_app.config.get('AI_MODEL', 'deepseek-chat'),
            messages=[
                {'role': 'system', 'content': prompt},
                {'role': 'user', 'content': '请为我生成一份适合的饮食方案。'},
            ],
            temperature=0.7,
            max_tokens=4096,
        )
        content = response.choices[0].message.content

        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
        raw_json = json_match.group(1).strip() if json_match else content.strip()

        # 修复可能的不合法 JSON
        plan_data = _repair_json_text(raw_json)
        if plan_data is None:
            # 仍然无法解析：返回原始文本，不保存脏数据
            return {
                'plan_content': content,
                'plan_data': {'raw_text': content},
                'total_cal': None,
            }

        # 确保 total_cal 存在（AI 可能漏掉）
        if isinstance(plan_data, dict) and not plan_data.get('total_cal'):
            plan_data['total_cal'] = user_info.get('recommend_cal', 1800)

        # 保存标准 JSON，避免前端解析失败
        plan_content = json.dumps(plan_data, ensure_ascii=False)

        return {
            'plan_content': plan_content,
            'plan_data': plan_data,
            'total_cal': plan_data.get('total_cal'),
        }
    except Exception as e:
        current_app.logger.error(f'AI方案生成失败，使用演示方案兜底: {str(e)}')
        return _mock_diet_plan(user_info)


def generate_weekly_report(user_info, weekly_stats, weight_records, diseases=None):
    days_logged = sum(1 for d in weekly_stats.get('daily', []) if d.get('cal', 0) > 0)
    avg_cal = weekly_stats.get('total_cal', 0) / max(days_logged, 1)

    weight_trend = ''
    if weight_records and len(weight_records) >= 2:
        start_w = weight_records[-1].weight
        end_w = weight_records[0].weight
        diff = end_w - start_w
        direction = '下降' if diff < 0 else '上升'
        weight_trend = f'本周体重变化：{start_w}kg -> {end_w}kg（{direction}{abs(diff):.1f}kg）'

    taboo_text = ''
    if diseases:
        lines = format_taboo_prompt(diseases)
        taboo_text = f'\n【用户饮食禁忌】评价与建议时请同时遵守以下禁忌：\n{lines}'

    prompt = f'''你是一个专业的减脂健康顾问。请根据用户的周饮食数据和体重变化，生成健康周报。

【用户信息】
- 身高：{user_info.get('height')}cm
- 当前体重：{user_info.get('current_weight')}kg
- 目标体重：{user_info.get('target_weight')}kg
- 推荐日摄入量：{user_info.get('recommend_cal')}kcal

【本周数据】
- 打卡天数：{days_logged}天
- 平均日摄入：{avg_cal:.0f}kcal
- 周总摄入：{weekly_stats.get('total_cal', 0)}kcal
{weight_trend}{taboo_text}

【要求】
1. 输出JSON格式，包含以下字段：
   - ai_comment: "对用户本周饮食和体重变化的健康评价（200字以内）"
   - score: 本周饮食评分(1-100)
   - suggest: "下周饮食改进建议（200字以内）"
2. 只输出JSON，不要有其他文字'''

    client = _get_client()
    if client is None:
        current_app.logger.warning('AI_API_KEY 未配置，使用演示周报兜底')
        return _mock_weekly_report(user_info, weekly_stats, weight_records)
    try:
        response = client.chat.completions.create(
            model=current_app.config.get('AI_MODEL', 'deepseek-chat'),
            messages=[
                {'role': 'system', 'content': prompt},
                {'role': 'user', 'content': '请分析我的本周数据并给出建议。'},
            ],
            temperature=0.7,
            max_tokens=2048,
        )
        content = response.choices[0].message.content

        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
        if json_match:
            report_data = json.loads(json_match.group(1))
        else:
            try:
                report_data = json.loads(content)
            except json.JSONDecodeError:
                report_data = {'ai_comment': content, 'suggest': ''}

        return {
            'ai_comment': report_data.get('ai_comment', content[:500]),
            'suggest': report_data.get('suggest', ''),
            'score': report_data.get('score'),
        }
    except Exception as e:
        current_app.logger.error(f'AI周报生成失败，使用演示周报兜底: {str(e)}')
        return _mock_weekly_report(user_info, weekly_stats, weight_records)
