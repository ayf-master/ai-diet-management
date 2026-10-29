"""W1 基线测量：跑当前 AI 方案 N 次，量化「热量误差 / 菜品是否在库里 / 延迟」。

用法（在项目根目录）：
    D:\\anaconda\\python.exe tools\\baseline_ai.py --runs 20

产物（默认写到项目根目录，已在 .gitignore）：
    baseline_ai_runs.csv    每次运行的明细
    baseline_ai_summary.json 汇总指标

指标定义：
- declared_cal_error：AI 自己报的 total_cal 与用户推荐热量的相对误差
- verified_cal_error：用数据库 nutrition 表按食材克数重算的热量，与推荐热量的相对误差
  （未在库中匹配到的食材按 0 计，因此该值同时反映「食材命中率」）
- dish_hit_rate：AI 输出的菜名中，能在 recipe 表里精确命中的比例
- food_hit_rate：AI 输出的食材名中，能在 food 表里精确命中的比例
- 这是「当前实现」的基线，不是目标值；后续 W2/W3 会把它降到可接受范围。
"""
import argparse
import csv
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))

from app import create_app, db  # noqa: E402
from models import Disease, Food, Nutrition, Recipe, User, UserDisease  # noqa: E402
from services.ai_service import generate_diet_plan  # noqa: E402

MEALS = ('breakfast', 'lunch', 'dinner', 'snack')


def _pct(value):
    return round(value * 100, 1)


def _load_diseases(user_id):
    """与 routes/ai.py 一致：把用户备注注入 Disease 供 prompt 使用。"""
    result = []
    for ud in UserDisease.query.filter_by(user_id=user_id).all():
        disease = db.session.get(Disease, ud.disease_id)
        if disease:
            disease.remark = ud.remark
            result.append(disease)
    return result


def _num(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _food_calorie_map():
    rows = db.session.query(Food.food_name, Nutrition.calorie) \
        .join(Nutrition, Nutrition.food_id == Food.food_id).all()
    return {name: calorie for name, calorie in rows if name}


def _recipe_names():
    return {name for (name,) in db.session.query(Recipe.recipe_name).all() if name}


def _measure(user, food_calories, recipe_names, diseases):
    started = time.perf_counter()
    result = generate_diet_plan(user.to_dict(), diseases)
    latency_ms = round((time.perf_counter() - started) * 1000)

    plan = result.get('plan_data') or {}
    declared_cal = _num(plan.get('total_cal') or result.get('total_cal'))
    recommend = _num(user.recommend_cal, 1800)

    dish_total = dish_hit = food_total = food_hit = 0
    verified_cal = 0.0
    for meal in MEALS:
        for dish in plan.get(meal) or []:
            dish_total += 1
            if dish.get('dish') in recipe_names:
                dish_hit += 1
            for item in dish.get('foods') or []:
                food_total += 1
                name = item.get('food')
                weight = _num(item.get('weight_g'))
                if name in food_calories:
                    food_hit += 1
                    verified_cal += food_calories[name] * weight / 100.0

    plan_text = result.get('plan_content') or ''
    return {
        'user_id': user.user_id,
        'account': user.account,
        'recommend_cal': recommend,
        'declared_cal': round(declared_cal),
        'verified_cal': round(verified_cal),
        'declared_error_pct': _pct(abs(declared_cal - recommend) / recommend) if recommend else None,
        'verified_error_pct': _pct(abs(verified_cal - recommend) / recommend) if recommend else None,
        'dish_total': dish_total,
        'dish_hit': dish_hit,
        'dish_hit_rate': _pct(dish_hit / dish_total) if dish_total else None,
        'food_total': food_total,
        'food_hit': food_hit,
        'food_hit_rate': _pct(food_hit / food_total) if food_total else None,
        'latency_ms': latency_ms,
        'is_mock': '演示方案' in plan_text or '演示数据' in plan_text,
    }


def _summary(rows):
    def median(key):
        vals = [r[key] for r in rows if r[key] is not None]
        return round(statistics.median(vals), 1) if vals else None

    def p95(key):
        vals = sorted(r[key] for r in rows if r[key] is not None)
        if not vals:
            return None
        idx = min(len(vals) - 1, int(round(len(vals) * 0.95)) - 1)
        return vals[max(idx, 0)]

    return {
        'runs': len(rows),
        'mock_runs': sum(1 for r in rows if r['is_mock']),
        'declared_cal_error_pct_median': median('declared_error_pct'),
        'verified_cal_error_pct_median': median('verified_error_pct'),
        'dish_hit_rate_pct_median': median('dish_hit_rate'),
        'food_hit_rate_pct_median': median('food_hit_rate'),
        'latency_ms_median': median('latency_ms'),
        'latency_ms_p95': p95('latency_ms'),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runs', type=int, default=20, help='运行次数（在用户间轮转）')
    parser.add_argument('--user-limit', type=int, default=5, help='最多取多少个用户')
    parser.add_argument('--out-prefix', default=str(ROOT / 'baseline_ai'))
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        users = User.query.order_by(User.user_id).limit(args.user_limit).all()
        if not users:
            raise SystemExit('数据库里没有用户，先导入种子数据')

        food_calories = _food_calorie_map()
        recipe_names = _recipe_names()
        print(f'用户 {len(users)} 个；食材 {len(food_calories)} 条；食谱 {len(recipe_names)} 条')

        rows = []
        for i in range(args.runs):
            user = users[i % len(users)]
            row = _measure(user, food_calories, recipe_names, _load_diseases(user.user_id))
            rows.append(row)
            print(
                f"[{i + 1}/{args.runs}] {user.account} "
                f"declared_err={row['declared_error_pct']}% "
                f"verified_err={row['verified_error_pct']}% "
                f"dish_hit={row['dish_hit_rate']}% "
                f"latency={row['latency_ms']}ms"
            )

        summary = _summary(rows)
        csv_path = Path(f'{args.out_prefix}_runs.csv')
        json_path = Path(f'{args.out_prefix}_summary.json')
        with csv_path.open('w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

        print('\n=== 基线汇总 ===')
        for key, value in summary.items():
            print(f'{key}: {value}')
        print(f'\n明细: {csv_path}')
        print(f'汇总: {json_path}')


if __name__ == '__main__':
    main()
