"""打卡/统计接口契约：薄路由仍保持旧契约。"""
from datetime import date


def test_meal_types_and_daily_stats_api(
    client, alice_token, auth_headers, seed_ids,
):
    headers = auth_headers(alice_token)

    types = client.get('/api/meal-types', headers=headers)
    assert types.status_code == 200
    assert '早餐' in [t['type_name'] for t in types.get_json()['data']]

    daily = client.get(
        f"/api/stats/daily?user_id={seed_ids['alice']}&date=2026-08-01",
        headers=headers,
    )
    assert daily.status_code == 200
    assert daily.get_json()['data']['total_cal'] == 133


def test_weekly_stats_api_returns_seven_days(client, alice_token, auth_headers, seed_ids):
    res = client.get(
        f"/api/stats/weekly?user_id={seed_ids['alice']}",
        headers=auth_headers(alice_token),
    )
    assert res.status_code == 200
    data = res.get_json()['data']
    assert len(data['daily']) == 7
    assert data['start'] <= data['end']


def test_create_meal_api_calculates_total(
    client, alice_token, auth_headers, seed_ids,
):
    res = client.post(
        '/api/meals',
        json={
            'meal_type_id': seed_ids['breakfast'],
            'eat_date': date.today().strftime('%Y-%m-%d'),
            'details': [{
                'recipe_id': seed_ids['system_recipe'],
                'eat_weight': 100,
                'oil_g': 10,
                'sauce_g': 5,
            }],
        },
        headers=auth_headers(alice_token),
    )
    assert res.status_code == 200
    data = res.get_json()['data']
    assert data['total_cal'] == 243

    client.delete(f"/api/meals/{data['record_id']}", headers=auth_headers(alice_token))
