"""W2 可信规划基线：跑 closed-set 管道，输出营养误差、候选数、修复/延迟。

用法（项目根目录）：
    D:\\anaconda\\python.exe tools\\baseline_w2.py --runs 5
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
from models import User  # noqa: E402
from services.health_check import load_user_diseases  # noqa: E402
from services.planning.candidates import MEAL_RATIOS  # noqa: E402
from services.planning.pipeline import generate_trusted_plan  # noqa: E402


def _pct(value):
    return round(value * 100, 1)


def _meal_balance(result):
    target = result.verification.target_cal
    worst = 0.0
    for meal, ratio in MEAL_RATIOS.items():
        if meal == 'snack':
            continue
        meal_target = target * ratio
        meal_cal = result.verification.meal_totals.get(meal, {}).get('cal', 0)
        if meal_target:
            worst = max(worst, abs(meal_cal - meal_target) / meal_target)
    return _pct(worst)


def _measure(user):
    started = time.perf_counter()
    result = generate_trusted_plan(user, load_user_diseases(user.user_id))
    elapsed = round((time.perf_counter() - started) * 1000)
    m = result.metrics
    return {
        'user_id': user.user_id,
        'account': user.account,
        'target_cal': m['target_cal'],
        'verified_cal': m['verified_cal'],
        'calorie_error_pct': m['calorie_error_pct'],
        'meal_balance_max_pct': _meal_balance(result),
        'protein_g': m['protein_g'],
        'candidate_count': m['candidate_count'],
        'attempts': m['attempts'],
        'status': m['status'],
        'source': m['source'],
        'model': m['model'],
        'schema_ok': m['schema_ok'],
        'invalid_id_count': m['invalid_id_count'],
        'repaired_count': m['repaired_count'],
        'danger_count': m['danger_count'],
        'fallback_used': m['fallback_used'],
        'latency_ms': m['latency_ms'],
        'wall_ms': elapsed,
    }


def _median(rows, key):
    values = [r[key] for r in rows if r[key] is not None]
    return round(statistics.median(values), 1) if values else None


def _p95(rows, key):
    values = sorted(r[key] for r in rows if r[key] is not None)
    if not values:
        return None
    idx = max(0, min(len(values) - 1, int(round(len(values) * 0.95)) - 1))
    return values[idx]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runs', type=int, default=5)
    parser.add_argument('--user-limit', type=int, default=5)
    parser.add_argument('--out-prefix', default=str(ROOT / 'baseline_w2'))
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        users = User.query.order_by(User.user_id).limit(args.user_limit).all()
        if not users:
            raise SystemExit('数据库里没有用户，先导入种子数据')

        rows = []
        for i in range(args.runs):
            user = users[i % len(users)]
            row = _measure(user)
            rows.append(row)
            print(
                f"[{i + 1}/{args.runs}] {user.account} "
                f"status={row['status']} err={row['calorie_error_pct']}% "
                f"meal_balance={row['meal_balance_max_pct']}% "
                f"candidates={row['candidate_count']} "
                f"repair={row['repaired_count']} latency={row['latency_ms']}ms"
            )

        summary = {
            'runs': len(rows),
            'status_counts': {
                s: sum(1 for r in rows if r['status'] == s)
                for s in ('ok', 'repaired', 'fallback')
            },
            'fallback_runs': sum(1 for r in rows if r['fallback_used']),
            'schema_ok_rate_pct': _pct(sum(1 for r in rows if r['schema_ok']) / len(rows)),
            'calorie_error_pct_median': _median(rows, 'calorie_error_pct'),
            'calorie_error_pct_p95': _p95(rows, 'calorie_error_pct'),
            'meal_balance_max_pct_median': _median(rows, 'meal_balance_max_pct'),
            'protein_g_median': _median(rows, 'protein_g'),
            'candidate_count_median': _median(rows, 'candidate_count'),
            'attempts_median': _median(rows, 'attempts'),
            'repaired_count_median': _median(rows, 'repaired_count'),
            'latency_ms_median': _median(rows, 'latency_ms'),
            'latency_ms_p95': _p95(rows, 'latency_ms'),
        }

        csv_path = Path(f'{args.out_prefix}_runs.csv')
        json_path = Path(f'{args.out_prefix}_summary.json')
        with csv_path.open('w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

        print('\n=== W2 汇总 ===')
        for key, value in summary.items():
            print(f'{key}: {value}')
        print(f'\n明细: {csv_path}')
        print(f'汇总: {json_path}')


if __name__ == '__main__':
    main()
