"""阶段 7.2 助手评估：10 条真实问题，统计工具命中、失败、DSML 重答与延迟。

用法（项目根目录）：
    D:\\anaconda\\python.exe tools\\eval_assistant.py
    D:\\anaconda\\python.exe tools\\eval_assistant.py --limit 3
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

from app import create_app  # noqa: E402
from models import Recipe, User  # noqa: E402
from services.agent.calling import run_single_turn  # noqa: E402

TOOL_MARKERS = ('DSML', '<|tool_calls', '<｜tool_calls')


def _pct(value):
    return round(value * 100, 1)


def _median(rows, key):
    values = [r[key] for r in rows if r[key] is not None]
    return round(statistics.median(values), 1) if values else None


def _p95(rows, key):
    values = sorted(r[key] for r in rows if r[key] is not None)
    if not values:
        return None
    idx = max(0, min(len(values) - 1, int(round(len(values) * 0.95)) - 1))
    return values[idx]


def _recipe_name(preferred, fallback):
    recipe = Recipe.query.filter_by(recipe_name=preferred).first()
    return recipe.recipe_name if recipe else fallback


def build_queries():
    tomato = _recipe_name('番茄炒鸡蛋', '番茄炒鸡蛋')
    chicken = _recipe_name('清蒸鸡胸肉', '清蒸鸡胸肉')
    broccoli = _recipe_name('水煮西兰花', '水煮西兰花')
    sandwich = _recipe_name('全麦三明治', '全麦三明治')
    oats = _recipe_name('燕麦牛奶粥', '燕麦牛奶粥')
    return [
        {
            'id': 'profile_cal',
            'question': '我的推荐热量是多少？',
            'expected_tool': 'get_user_profile',
        },
        {
            'id': 'profile_goal',
            'question': '我的减脂目标是什么？',
            'expected_tool': 'get_user_profile',
        },
        {
            'id': 'lunch_candidates',
            'question': '午餐可以吃什么？给我两个候选，并说明热量。',
            'expected_tool': 'search_recipes',
        },
        {
            'id': 'dinner_candidates',
            'question': '晚餐有什么推荐？',
            'expected_tool': 'search_recipes',
        },
        {
            'id': 'breakfast_candidates',
            'question': '早餐有哪些选择？',
            'expected_tool': 'search_recipes',
        },
        {
            'id': 'low_cal_lunch',
            'question': '我想吃低热量午餐，推荐两个。',
            'expected_tool': 'search_recipes',
        },
        {
            'id': 'tomato_cal',
            'question': f'{tomato} 200 克热量多少？',
            'expected_tool': 'calculate_recipe_nutrition',
        },
        {
            'id': 'chicken_protein',
            'question': f'{chicken} 150 克含多少蛋白质？',
            'expected_tool': 'calculate_recipe_nutrition',
        },
        {
            'id': 'broccoli_cal',
            'question': f'{broccoli} 300 克的热量是多少？',
            'expected_tool': 'calculate_recipe_nutrition',
        },
        {
            'id': 'compare_breakfast',
            'question': f'{sandwich}和{oats}哪个热量低？',
            'expected_tool': 'calculate_recipe_nutrition',
        },
    ]


def _measure(user, item):
    started = time.perf_counter()
    result = run_single_turn(user, item['question'])
    wall_ms = round((time.perf_counter() - started) * 1000)

    names = [call['name'] for call in result.tool_calls]
    successful_names = [call['name'] for call in result.tool_calls if call['ok']]
    tool_errors = [call for call in result.tool_calls if not call['ok']]
    dsml_retry = any(event.get('event') == 'final_answer_invalid' for event in result.trace)
    markup = any(marker in (result.answer or '') for marker in TOOL_MARKERS)
    success = bool(
        result.ok
        and result.answer
        and not markup
        and result.status not in ('degraded', 'model_error', 'invalid_request', 'unavailable')
    )

    return {
        'id': item['id'],
        'question': item['question'],
        'status': result.status,
        'ok': result.ok,
        'success': success,
        'expected_tool': item['expected_tool'],
        'expected_hit': item['expected_tool'] in successful_names,
        'tool_calls': ','.join(names),
        'tool_call_count': len(names),
        'tool_success_count': len(successful_names),
        'tool_error_count': len(tool_errors),
        'tool_rounds': result.tool_rounds,
        'attempts': result.attempts,
        'tool_retry': result.tool_rounds > 1,
        'dsml_retry': dsml_retry,
        'markup': markup,
        'answer_chars': len(result.answer or ''),
        'latency_ms': wall_ms,
        'model': result.model,
        'error': result.error,
        'answer_preview': (result.answer or '').replace('\n', ' ')[:160],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--account', default='', help='默认取 user_id 最小的用户')
    parser.add_argument('--out-prefix', default=str(ROOT / 'baseline_assistant'))
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        if args.account:
            user = User.query.filter_by(account=args.account).first()
        else:
            user = User.query.order_by(User.user_id).first()
        if user is None:
            raise SystemExit('数据库里没有用户，先导入种子数据')

        queries = build_queries()[:max(1, args.limit)]
        print(f'用户：{user.account} (id={user.user_id})，问题数：{len(queries)}')

        rows = []
        for index, item in enumerate(queries, start=1):
            row = _measure(user, item)
            rows.append(row)
            print(
                f"[{index}/{len(queries)}] {row['id']} "
                f"status={row['status']} hit={row['expected_hit']} "
                f"tools={row['tool_calls'] or '-'} "
                f"dsml_retry={row['dsml_retry']} latency={row['latency_ms']}ms"
            )
            if not row['success']:
                print(f"  ! {row['error'] or 'answer invalid'}: {row['answer_preview']}")

        summary = {
            'model': rows[0]['model'] if rows else '',
            'queries': len(rows),
            'success_rate_pct': _pct(sum(1 for r in rows if r['success']) / len(rows)),
            'expected_tool_hit_rate_pct': _pct(
                sum(1 for r in rows if r['expected_hit']) / len(rows)
            ),
            'tool_error_rate_pct': _pct(
                sum(1 for r in rows if r['tool_error_count'] > 0) / len(rows)
            ),
            'dsml_retry_rate_pct': _pct(
                sum(1 for r in rows if r['dsml_retry']) / len(rows)
            ),
            'tool_retry_rate_pct': _pct(
                sum(1 for r in rows if r['tool_retry']) / len(rows)
            ),
            'degraded_rate_pct': _pct(
                sum(1 for r in rows if r['status'] == 'degraded') / len(rows)
            ),
            'avg_tool_calls': round(
                sum(r['tool_call_count'] for r in rows) / len(rows), 2
            ),
            'latency_ms_median': _median(rows, 'latency_ms'),
            'latency_ms_p95': _p95(rows, 'latency_ms'),
            'status_counts': {
                status: sum(1 for r in rows if r['status'] == status)
                for status in sorted({r['status'] for r in rows})
            },
        }

        csv_path = Path(f'{args.out_prefix}_runs.csv')
        json_path = Path(f'{args.out_prefix}_summary.json')
        with csv_path.open('w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

        print('\n=== 助手评估汇总 ===')
        for key, value in summary.items():
            print(f'{key}: {value}')
        print(f'\n明细: {csv_path}')
        print(f'汇总: {json_path}')


if __name__ == '__main__':
    main()
