"""meal_service 单测：打卡热量、可见性、删除归属。"""
from datetime import date

import pytest

from app import db
from models import DietRecord
from services import meal_service, stats_service
from services.errors import DomainError


def test_create_meal_computes_single_calorie_and_total(app, seed_ids):
    with app.app_context():
        record = meal_service.create_meal(
            {
                'meal_type_id': seed_ids['breakfast'],
                'eat_date': '2026-08-04',
                'details': [
                    {'recipe_id': seed_ids['system_recipe'], 'eat_weight': 50},
                ],
            },
            user_id=seed_ids['alice'],
        )
        assert record.total_cal == 66
        assert len(record.details) == 1
        assert record.details[0].single_cal == 66
        assert record.details[0].oil_g == 0
        assert record.details[0].sauce_g == 0


def test_create_meal_uses_override_oil_and_sauce(app, seed_ids):
    with app.app_context():
        record = meal_service.create_meal(
            {
                'meal_type_id': seed_ids['breakfast'],
                'eat_date': '2026-08-04',
                'details': [{
                    'recipe_id': seed_ids['system_recipe'],
                    'eat_weight': 100,
                    'oil_g': 10,
                    'sauce_g': 5,
                }],
            },
            user_id=seed_ids['alice'],
        )
        assert record.total_cal == 243
        assert record.details[0].oil_g == 10
        assert record.details[0].sauce_g == 5


def test_meal_of_others_recipe_is_skipped(app, seed_ids):
    with app.app_context():
        # Bob 的食谱对 Alice 不可见；当前实现是跳过而不是报错
        from services import recipe_service
        bob_recipe = recipe_service.create_recipe(
            {'recipe_name': 'Bob 私房菜', 'ingredients': []},
            owner_id=seed_ids['bob'],
            admin_id=None,
        )
        record = meal_service.create_meal(
            {
                'meal_type_id': seed_ids['breakfast'],
                'eat_date': '2026-08-04',
                'details': [{'recipe_id': bob_recipe.recipe_id, 'eat_weight': 100}],
            },
            user_id=seed_ids['alice'],
        )
        assert record.total_cal == 0
        assert record.details == []


def test_daily_and_weekly_stats(app, seed_ids):
    with app.app_context():
        meal_service.create_meal(
            {
                'meal_type_id': seed_ids['breakfast'],
                'eat_date': '2026-08-04',
                'details': [{'recipe_id': seed_ids['system_recipe'], 'eat_weight': 50}],
            },
            user_id=seed_ids['bob'],
        )

        daily = stats_service.daily_stats(seed_ids['bob'], '2026-08-04')
        assert daily['total_cal'] == 66
        assert daily['meal_count'] == 1
        assert daily['meals'][0]['meal_type'] == '早餐'

        weekly = stats_service.weekly_stats(seed_ids['bob'], end=date(2026, 8, 7))
        assert weekly['start'] == '2026-08-01'
        assert weekly['end'] == '2026-08-07'
        assert len(weekly['daily']) == 7
        assert weekly['total_cal'] == 166       # 种子 100 + 本次 66
        by_date = {item['date']: item['cal'] for item in weekly['daily']}
        assert by_date['2026-08-01'] == 100
        assert by_date['2026-08-04'] == 66


def test_delete_meal_enforces_owner(app, seed_ids):
    with app.app_context():
        record = meal_service.create_meal(
            {
                'meal_type_id': seed_ids['breakfast'],
                'eat_date': '2026-08-04',
                'details': [],
            },
            user_id=seed_ids['alice'],
        )
        record_id = record.record_id

        with pytest.raises(DomainError) as exc:
            meal_service.delete_meal(
                record_id, viewer_id=seed_ids['bob'], viewer_is_admin=False,
            )
        assert exc.value.code == 403

        meal_service.delete_meal(
            record_id, viewer_id=seed_ids['alice'], viewer_is_admin=False,
        )
        assert db.session.get(DietRecord, record_id) is None


def test_weekly_weight_records_and_diff(app, seed_ids):
    with app.app_context():
        from models import WeightRecord
        db.session.add_all([
            WeightRecord(user_id=seed_ids['alice'], weight=60, measure_date='2026-08-02'),
            WeightRecord(user_id=seed_ids['alice'], weight=59.5, measure_date='2026-08-05'),
        ])
        db.session.commit()

        records = stats_service.weight_records_between(
            seed_ids['alice'], date(2026, 8, 1), date(2026, 8, 7),
        )
        assert len(records) == 2
        assert stats_service.weight_diff(records) == -0.5
