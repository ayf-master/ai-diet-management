"""食材可见性：普通用户只看系统 + 自己，管理员看全部。"""


def _names(res):
    return {f['food_name'] for f in res.get_json()['data']}


def test_user_sees_system_and_own_only(client, alice_token, auth_headers):
    res = client.get('/api/foods', headers=auth_headers(alice_token))
    assert res.status_code == 200
    names = _names(res)
    assert '系统鸡胸肉' in names
    assert 'Alice 的燕麦' in names
    assert 'Bob 的香蕉' not in names


def test_admin_sees_all_foods(client, admin_token, auth_headers):
    res = client.get('/api/foods', headers=auth_headers(admin_token))
    assert res.status_code == 200
    names = _names(res)
    assert {'系统鸡胸肉', 'Alice 的燕麦', 'Bob 的香蕉'} <= names


def test_user_cannot_read_others_food(client, alice_token, auth_headers, seed_ids):
    res = client.get(
        f"/api/foods/{seed_ids['bob_food']}", headers=auth_headers(alice_token),
    )
    assert res.status_code == 404


def test_user_cannot_query_other_users_scope(client, alice_token, auth_headers, seed_ids):
    res = client.get(
        f"/api/foods?user_id={seed_ids['bob']}", headers=auth_headers(alice_token),
    )
    assert res.status_code == 403


def test_user_cannot_create_system_food(client, alice_token, auth_headers):
    res = client.post(
        '/api/foods', json={'food_name': '用户想建的系统食材'}, headers=auth_headers(alice_token),
    )
    assert res.status_code == 403


def test_user_can_create_own_food(client, alice_token, auth_headers, seed_ids):
    res = client.post(
        '/api/foods',
        json={'food_name': 'Alice 的酸奶', 'user_id': seed_ids['alice']},
        headers=auth_headers(alice_token),
    )
    assert res.status_code == 200
    assert res.get_json()['data']['user_id'] == seed_ids['alice']


def test_admin_can_create_system_food_and_user_sees_it(client, admin_token, alice_token, auth_headers):
    res = client.post(
        '/api/foods', json={'food_name': '管理员新增的系统食材'}, headers=auth_headers(admin_token),
    )
    assert res.status_code == 200
    assert res.get_json()['data']['user_id'] is None

    names = _names(client.get('/api/foods', headers=auth_headers(alice_token)))
    assert '管理员新增的系统食材' in names
