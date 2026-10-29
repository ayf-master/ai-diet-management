"""资源归属：跨用户读写必须 403，自己的资源可以正常改删。"""


def test_cannot_update_or_delete_others_food(client, alice_token, auth_headers, seed_ids):
    headers = auth_headers(alice_token)
    food_id = seed_ids['bob_food']

    assert client.put(
        f'/api/foods/{food_id}', json={'food_name': '被改了'}, headers=headers,
    ).status_code == 403
    assert client.delete(f'/api/foods/{food_id}', headers=headers).status_code == 403


def test_cannot_delete_system_food(client, alice_token, auth_headers, seed_ids):
    res = client.delete(
        f"/api/foods/{seed_ids['system_food']}", headers=auth_headers(alice_token),
    )
    assert res.status_code == 403


def test_cannot_delete_others_meal(client, alice_token, auth_headers, seed_ids):
    res = client.delete(
        f"/api/meals/{seed_ids['bob_meal']}", headers=auth_headers(alice_token),
    )
    assert res.status_code == 403


def test_cannot_delete_others_weight(client, alice_token, auth_headers, seed_ids):
    res = client.delete(
        f"/api/weight/{seed_ids['bob_weight']}", headers=auth_headers(alice_token),
    )
    assert res.status_code == 403


def test_cannot_delete_others_ai_plan(client, alice_token, auth_headers, seed_ids):
    res = client.delete(
        f"/api/ai/plan/{seed_ids['bob_plan']}", headers=auth_headers(alice_token),
    )
    assert res.status_code == 403


def test_cannot_delete_others_recipe(client, bob_token, auth_headers, seed_ids):
    res = client.delete(
        f"/api/recipes/{seed_ids['alice_recipe']}", headers=auth_headers(bob_token),
    )
    assert res.status_code == 403


def test_cannot_modify_system_recipe(client, alice_token, auth_headers, seed_ids):
    res = client.delete(
        f"/api/recipes/{seed_ids['system_recipe']}", headers=auth_headers(alice_token),
    )
    assert res.status_code == 403


def test_owner_can_delete_own_meal(client, alice_token, auth_headers, seed_ids):
    headers = auth_headers(alice_token)
    created = client.post(
        '/api/meals',
        json={'details': [{'recipe_id': seed_ids['system_recipe'], 'eat_weight': 100}]},
        headers=headers,
    )
    assert created.status_code == 200
    record_id = created.get_json()['data']['record_id']

    res = client.delete(f'/api/meals/{record_id}', headers=headers)
    assert res.status_code == 200

    meals = client.get(f"/api/meals?user_id={seed_ids['alice']}", headers=headers).get_json()['data']
    assert all(m['record_id'] != record_id for m in meals)


def test_meal_create_for_other_user_forbidden(client, alice_token, auth_headers, seed_ids):
    res = client.post(
        '/api/meals',
        json={'user_id': seed_ids['bob'], 'details': []},
        headers=auth_headers(alice_token),
    )
    assert res.status_code == 403


def test_meal_create_without_user_id_uses_token_identity(
    client, alice_token, auth_headers, seed_ids,
):
    res = client.post(
        '/api/meals',
        json={'details': [{'recipe_id': seed_ids['system_recipe'], 'eat_weight': 100}]},
        headers=auth_headers(alice_token),
    )
    assert res.status_code == 200
    assert res.get_json()['data']['user_id'] == seed_ids['alice']


def test_weight_create_for_other_user_forbidden(client, alice_token, auth_headers, seed_ids):
    res = client.post(
        '/api/weight',
        json={'user_id': seed_ids['bob'], 'weight': 70},
        headers=auth_headers(alice_token),
    )
    assert res.status_code == 403


def test_weight_create_and_read_self(client, alice_token, auth_headers, seed_ids):
    headers = auth_headers(alice_token)
    assert client.post('/api/weight', json={'weight': 59.5}, headers=headers).status_code == 200

    latest = client.get(
        f"/api/weight/latest?user_id={seed_ids['alice']}", headers=headers,
    ).get_json()['data']
    assert latest['weight'] == 59.5
