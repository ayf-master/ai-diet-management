"""食谱接口契约：薄路由 + 领域异常 → HTTP 的映射。"""
import uuid


def test_duplicate_recipe_api_returns_409(client, alice_token, auth_headers):
    name = f'接口重名-{uuid.uuid4().hex[:6]}'
    headers = auth_headers(alice_token)
    payload = {'recipe_name': name, 'type': '午餐', 'ingredients': []}

    assert client.post('/api/recipes', json=payload, headers=headers).status_code == 200
    res = client.post('/api/recipes', json=payload, headers=headers)
    assert res.status_code == 409
    assert res.get_json()['code'] == 409


def test_update_others_recipe_api_returns_403(
    client, bob_token, auth_headers, seed_ids,
):
    res = client.put(
        f"/api/recipes/{seed_ids['alice_recipe']}",
        json={'recipe_name': '越权改名'},
        headers=auth_headers(bob_token),
    )
    assert res.status_code == 403


def test_get_others_recipe_api_returns_404(
    client, bob_token, auth_headers, seed_ids,
):
    res = client.get(
        f"/api/recipes/{seed_ids['alice_recipe']}",
        headers=auth_headers(bob_token),
    )
    assert res.status_code == 404
