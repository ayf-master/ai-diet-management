"""统计用例：日/周饮食聚合与体重区间查询，供 meal 路由和 AI 周报共用。"""
from datetime import date, timedelta

from models import DietRecord, WeightRecord


def week_range(end=None):
    """返回最近 7 天的 (start_date, end_date)，含今天。"""
    end_date = end or date.today()
    return end_date - timedelta(days=6), end_date


def daily_stats(user_id, date_str=None):
    date_str = date_str or date.today().strftime('%Y-%m-%d')
    records = DietRecord.query.filter_by(user_id=user_id, eat_date=date_str).all()
    return {
        'date': date_str,
        'total_cal': sum((r.total_cal or 0) for r in records),
        'meal_count': len(records),
        'meals': [
            {
                'meal_type': r.meal_type.type_name if r.meal_type else None,
                'cal': r.total_cal or 0,
            }
            for r in records
        ],
    }


def weekly_stats(user_id, end=None):
    start, end_date = week_range(end)
    records = DietRecord.query.filter(
        DietRecord.user_id == user_id,
        DietRecord.eat_date.between(start, end_date),
    ).order_by(DietRecord.eat_date).all()

    daily_data = {}
    for record in records:
        day = str(record.eat_date)
        daily_data[day] = daily_data.get(day, 0) + (record.total_cal or 0)

    week = [
        (start + timedelta(days=i)).strftime('%Y-%m-%d')
        for i in range(7)
    ]
    return {
        'start': str(start),
        'end': str(end_date),
        'total_cal': sum((r.total_cal or 0) for r in records),
        'daily': [{'date': d, 'cal': daily_data.get(d, 0)} for d in week],
    }


def weight_records_between(user_id, start, end):
    return WeightRecord.query.filter(
        WeightRecord.user_id == user_id,
        WeightRecord.measure_date.between(start, end),
    ).order_by(WeightRecord.measure_date).all()


def weight_diff(records):
    if records and len(records) >= 2:
        return round(records[-1].weight - records[0].weight, 1)
    return 0
