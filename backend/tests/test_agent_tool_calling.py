"""阶段 7.2：单轮 Tool Calling 协议、消息回填与有界重试。"""
import json
from types import SimpleNamespace

from app import db
from models import User
from services.agent.calling import SingleTurnResult, run_single_turn
from services.agent.tools import TOOL_REGISTRY, to_openai_tool


class FakeCompletions:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if not self.responses:
            raise AssertionError('unexpected extra model call')
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class FakeClient:
    def __init__(self, responses):
        self.completions = FakeCompletions(responses)
        self.chat = SimpleNamespace(completions=self.completions)


def _tool_call(call_id, name, arguments):
    if not isinstance(arguments, str):
        arguments = json.dumps(arguments, ensure_ascii=False)
    return SimpleNamespace(
        id=call_id,
        type='function',
        function=SimpleNamespace(name=name, arguments=arguments),
    )


def _response(content=None, tool_calls=None):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
        content=content,
        tool_calls=tool_calls,
    ))])


def test_toolspec_converts_to_function_schema():
    schema = to_openai_tool(TOOL_REGISTRY.get('search_recipes'))
    params = schema['function']['parameters']

    assert schema['type'] == 'function'
    assert schema['function']['name'] == 'search_recipes'
    assert params['type'] == 'object'
    assert params['additionalProperties'] is False
    assert params['required'] == ['meal_type']
    assert params['properties']['meal_type']['enum'] == [
        'breakfast', 'lunch', 'dinner', 'snack',
    ]
    assert params['properties']['limit']['maximum'] == 8
    assert 'user_id' not in params['properties']


def test_no_tool_call_returns_direct_answer(app, seed_ids):
    fake = FakeClient([_response('直接回答')])
    with app.app_context():
        alice = db.session.get(User, seed_ids['alice'])
        result = run_single_turn(alice, '你好', client=fake)

        assert result.ok is True
        assert result.status == 'answered'
        assert result.answer == '直接回答'
        assert result.attempts == 1
        assert result.tool_rounds == 0
        assert fake.completions.calls[0]['tools']
        assert [m['role'] for m in fake.completions.calls[0]['messages']] == ['system', 'user']


def test_single_tool_call_is_executed_and_observation_is_returned(app, seed_ids):
    fake = FakeClient([
        _response(tool_calls=[_tool_call('call_1', 'get_user_profile', {})]),
        _response('你的推荐摄入是 1500 kcal。'),
    ])
    with app.app_context():
        alice = db.session.get(User, seed_ids['alice'])
        result = run_single_turn(alice, '我的目标是什么？', client=fake)

        assert result.status == 'tool_answered'
        assert result.attempts == 2
        assert result.tool_rounds == 1
        assert result.tool_calls[0]['name'] == 'get_user_profile'
        assert result.tool_calls[0]['ok'] is True

        first_call = fake.completions.calls[0]
        second_call = fake.completions.calls[1]
        assert first_call['tools']
        assert second_call['tools']
        assert second_call['tool_choice'] == 'none'
        assert [m['role'] for m in second_call['messages']] == [
            'system', 'user', 'assistant', 'tool',
        ]
        assert second_call['messages'][2]['tool_calls'][0]['id'] == 'call_1'
        assert second_call['messages'][3]['tool_call_id'] == 'call_1'
        assert 'recommend_cal' in second_call['messages'][3]['content']


def test_final_tool_markup_is_retried_in_clean_context(app, seed_ids):
    fake = FakeClient([
        _response(tool_calls=[_tool_call('call_1', 'get_user_profile', {})]),
        _response('<｜DSML｜tool_calls><｜DSML｜invoke name="search_recipes">'),
        _response('你的推荐摄入是 1500 kcal。'),
    ])
    with app.app_context():
        alice = db.session.get(User, seed_ids['alice'])
        result = run_single_turn(alice, '我该吃多少？', client=fake)

        assert result.status == 'repaired'
        assert result.attempts == 3
        assert result.tool_rounds == 1
        assert result.answer == '你的推荐摄入是 1500 kcal。'
        assert 'tools' not in fake.completions.calls[2]
        assert [m['role'] for m in fake.completions.calls[2]['messages']] == ['system', 'user']
        assert any(e['event'] == 'final_answer_invalid' for e in result.trace)


def test_parallel_tool_calls_get_one_tool_message_each(app, seed_ids):
    fake = FakeClient([
        _response(tool_calls=[
            _tool_call('call_a', 'get_user_profile', {}),
            _tool_call('call_b', 'search_recipes', {'meal_type': 'lunch', 'limit': 2}),
        ]),
        _response('找到 2 个午餐候选。'),
    ])
    with app.app_context():
        alice = db.session.get(User, seed_ids['alice'])
        result = run_single_turn(alice, '午餐吃什么？', client=fake)

        assert result.status == 'tool_answered'
        assert len(result.tool_calls) == 2
        assert {r['name'] for r in result.tool_calls} == {'get_user_profile', 'search_recipes'}

        messages = fake.completions.calls[1]['messages']
        assert [m['role'] for m in messages] == [
            'system', 'user', 'assistant', 'tool', 'tool',
        ]
        assert [m['tool_call_id'] for m in messages[3:]] == ['call_a', 'call_b']


def test_malformed_arguments_are_reported_then_model_can_repair(app, seed_ids):
    fake = FakeClient([
        _response(tool_calls=[_tool_call('call_bad', 'search_recipes', '{not-json')]),
        _response('抱歉，参数格式有问题。'),
    ])
    with app.app_context():
        alice = db.session.get(User, seed_ids['alice'])
        result = run_single_turn(alice, '搜索午餐', client=fake)

        assert result.status == 'repaired'
        assert result.attempts == 2
        assert result.tool_rounds == 1
        assert result.tool_calls[0]['ok'] is False
        assert result.tool_calls[0]['error_code'] == 'invalid_arguments'
        assert fake.completions.calls[1]['tools']


def test_failed_tool_gets_one_retry_then_final_answer(app, seed_ids):
    fake = FakeClient([
        _response(tool_calls=[_tool_call('call_bad', 'delete_everything', {})]),
        _response(tool_calls=[_tool_call('call_ok', 'get_user_profile', {})]),
        _response('这是你的资料。'),
    ])
    with app.app_context():
        alice = db.session.get(User, seed_ids['alice'])
        result = run_single_turn(alice, '查我的资料', client=fake)

        assert result.status == 'repaired'
        assert result.attempts == 3
        assert result.tool_rounds == 2
        assert result.tool_calls[0]['error_code'] == 'unknown_tool'
        assert result.tool_calls[1]['ok'] is True
        assert fake.completions.calls[2]['tool_choice'] == 'none'


def test_retry_is_bounded_to_one_extra_round(app, seed_ids):
    fake = FakeClient([
        _response(tool_calls=[_tool_call('call_1', 'delete_everything', {})]),
        _response(tool_calls=[_tool_call('call_2', 'delete_everything', {})]),
        _response('这次查询没有成功。'),
    ])
    with app.app_context():
        alice = db.session.get(User, seed_ids['alice'])
        result = run_single_turn(alice, '查资料', client=fake)

        assert result.status == 'degraded'
        assert result.attempts == 3
        assert result.tool_rounds == 2
        assert result.error == 'tool_failed'
        assert len(result.tool_calls) == 2
        assert all(not r['ok'] for r in result.tool_calls)


def test_identity_injection_is_rejected_and_retried(app, seed_ids):
    fake = FakeClient([
        _response(tool_calls=[_tool_call(
            'call_1', 'get_user_profile', {'user_id': seed_ids['bob']},
        )]),
        _response('我不能读取其他用户的数据。'),
    ])
    with app.app_context():
        alice = db.session.get(User, seed_ids['alice'])
        result = run_single_turn(alice, '查 Bob 的资料', client=fake)

        assert result.tool_calls[0]['error_code'] == 'invalid_arguments'
        assert result.status == 'repaired'


def test_model_failure_returns_model_error_without_tool_calls(app, seed_ids):
    fake = FakeClient([RuntimeError('upstream down')])
    with app.app_context():
        alice = db.session.get(User, seed_ids['alice'])
        result = run_single_turn(alice, '你好', client=fake)

        assert result.ok is False
        assert result.status == 'model_error'
        assert result.attempts == 1
        assert result.tool_calls == []
        assert result.error == 'model_failed'


def test_assistant_api_returns_single_turn_payload(
    app, client, alice_token, auth_headers, monkeypatch,
):
    def fake_run(user, message):
        return SingleTurnResult(
            answer='测试回答',
            status='answered',
            ok=True,
            attempts=1,
            model='fake',
        )

    monkeypatch.setattr('routes.ai.run_single_turn', fake_run)
    res = client.post(
        '/api/ai/assistant',
        json={'message': '你好'},
        headers=auth_headers(alice_token),
    )

    assert res.status_code == 200
    body = res.get_json()
    assert body['data']['answer'] == '测试回答'
    assert body['data']['status'] == 'answered'
