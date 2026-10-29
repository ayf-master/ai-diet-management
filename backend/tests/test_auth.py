"""鉴权边界：没有 token 一律 401，token 只能代表自己。"""


def test_protected_endpoint_rejects_missing_token(client):
    res = client.get('/api/foods')
    assert res.status_code == 401
    assert res.get_json()['code'] == 401


def test_protected_endpoint_rejects_invalid_token(client):
    res = client.get('/api/foods', headers={'Authorization': 'Bearer not-a-real-jwt'})
    assert res.status_code == 401


def test_login_returns_usable_token(client, auth_headers):
    res = client.post('/api/login', json={'account': 'alice', 'password': 'pass1234'})
    assert res.status_code == 200
    body = res.get_json()
    assert body['access_token']

    ok = client.get('/api/foods', headers=auth_headers(body['access_token']))
    assert ok.status_code == 200


def test_login_rejects_wrong_password(client):
    res = client.post('/api/login', json={'account': 'alice', 'password': 'wrong'})
    assert res.status_code == 401


def test_register_returns_token_and_self_scope(client, auth_headers):
    res = client.post('/api/register', json={'account': 'carol', 'password': 'pass1234'})
    assert res.status_code == 200, res.get_json()
    body = res.get_json()
    assert body['access_token']
    uid = body['data']['user_id']

    headers = auth_headers(body['access_token'])
    assert client.get(f'/api/user/profile?user_id={uid}', headers=headers).status_code == 200
    assert client.get('/api/user/profile?user_id=1', headers=headers).status_code == 403


def test_cross_user_profile_is_forbidden(client, alice_token, auth_headers, seed_ids):
    res = client.get(
        f"/api/user/profile?user_id={seed_ids['bob']}",
        headers=auth_headers(alice_token),
    )
    assert res.status_code == 403
    assert res.get_json()['code'] == 403


def test_admin_can_read_any_profile(client, admin_token, auth_headers, seed_ids):
    res = client.get(
        f"/api/user/profile?user_id={seed_ids['bob']}",
        headers=auth_headers(admin_token),
    )
    assert res.status_code == 200


def test_user_cannot_issue_admin_scope(client, alice_token, auth_headers):
    # 普通用户伪造 role=admin 也没用：服务端只信自己签发的 token
    res = client.post(
        '/api/foods',
        json={'food_name': '越权系统食材'},
        headers=auth_headers(alice_token),
    )
    assert res.status_code == 403
