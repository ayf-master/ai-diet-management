"""可信规划编排：闭集校验、有界修复、重生成与指标。"""
import json

from app import db
from models import AiPlanRun, User
from services.planning.pipeline import generate_trusted_plan


def _valid_plan(seed_ids):
    return {
        'breakfast': [{'recipe_id': seed_ids['system_recipe'], 'weight_g': 250}],
        'lunch': [{'recipe_id': seed_ids['system_lunch'], 'weight_g': 500}],
        'dinner': [{'recipe_id': seed_ids['system_dinner'], 'weight_g': 400}],
        'snack': [],
        'tips': '测试方案',
    }


def _provider(plan):
    def provide(user_info, diseases, candidates, correction=None):
        return {
            'raw_text': json.dumps(plan, ensure_ascii=False),
            'plan_data': plan,
            'source': 'model',
            'model': 'fake',
        }
    return provide


def test_pipeline_accepts_valid_closed_set_selection(app, seed_ids):
    with app.app_context():
        alice = db.session.get(User, seed_ids['alice'])
        result = generate_trusted_plan(
            alice, [], selection_provider=_provider(_valid_plan(seed_ids)),
        )

        assert result.verification.ok
        assert result.metrics['status'] == 'ok'
        assert result.metrics['candidate_count'] == 6
        assert result.metrics['invalid_id_count'] == 0
        assert result.metrics['calorie_error_pct'] <= 5
        assert result.metrics['verified_cal'] == 1530
        assert result.plan['total_cal'] == 1530
        assert result.plan['verification']['ok'] is True
        assert result.plan['lunch'][0]['dish'] == '系统午餐'
        assert result.plan['lunch'][0]['foods'][0]['food'] == '系统鸡胸肉'


def test_pipeline_repairs_invalid_ids_with_candidates(app, seed_ids):
    bad = {
        'breakfast': [{'recipe_id': 999999, 'weight_g': 100}],
        'lunch': [],
        'dinner': [],
        'snack': [],
    }
    with app.app_context():
        alice = db.session.get(User, seed_ids['alice'])
        result = generate_trusted_plan(
            alice, [], selection_provider=_provider(bad),
        )

        selected = [
            dish.recipe_id
            for meal in ('breakfast', 'lunch', 'dinner', 'snack')
            for dish in getattr(result.selection, meal)
        ]
        assert 999999 not in selected
        assert selected
        assert result.metrics['invalid_id_count'] == 1
        assert result.metrics['repaired_count'] >= 1
        assert result.metrics['status'] in ('repaired', 'fallback')


def test_pipeline_regenerates_once_when_schema_invalid(app, seed_ids):
    calls = []
    malformed = {
        'breakfast': [{'recipe_id': seed_ids['system_recipe']}],
        'lunch': [], 'dinner': [], 'snack': [],
    }

    def provide(user_info, diseases, candidates, correction=None):
        calls.append(correction)
        plan = malformed if len(calls) == 1 else _valid_plan(seed_ids)
        return {
            'raw_text': json.dumps(plan, ensure_ascii=False),
            'plan_data': plan,
            'source': 'model',
            'model': 'fake',
        }

    with app.app_context():
        alice = db.session.get(User, seed_ids['alice'])
        result = generate_trusted_plan(alice, [], selection_provider=provide)

        assert len(calls) == 2
        assert calls[1] is not None
        assert result.attempts == 2
        assert result.metrics['schema_ok'] is True
        assert result.metrics['status'] == 'ok'


def test_pipeline_scales_under_target_selection(app, seed_ids):
    under = {
        'breakfast': [{'recipe_id': seed_ids['system_recipe'], 'weight_g': 100}],
        'lunch': [{'recipe_id': seed_ids['system_lunch'], 'weight_g': 200}],
        'dinner': [{'recipe_id': seed_ids['system_dinner'], 'weight_g': 200}],
        'snack': [],
    }
    with app.app_context():
        alice = db.session.get(User, seed_ids['alice'])
        result = generate_trusted_plan(
            alice, [], selection_provider=_provider(under),
        )

        assert result.metrics['status'] == 'repaired'
        assert result.metrics['calorie_error_pct'] <= 5
        assert result.metrics['verified_cal'] > 1000
        assert result.verification.ok


def test_ai_plan_api_persists_plan_and_run_metrics(
    app, client, alice_token, auth_headers, seed_ids, monkeypatch,
):
    monkeypatch.setattr(
        'services.planning.pipeline.generate_selection',
        _provider(_valid_plan(seed_ids)),
    )
    res = client.post(
        '/api/ai/plan',
        json={'user_id': seed_ids['alice']},
        headers=auth_headers(alice_token),
    )
    assert res.status_code == 200

    data = res.get_json()['data']
    plan = json.loads(data['plan_content'])
    assert plan['total_cal'] == 1530
    assert data['verification']['ok'] is True

    with app.app_context():
        run = AiPlanRun.query.filter_by(user_id=seed_ids['alice']).order_by(
            AiPlanRun.run_id.desc()
        ).first()
        assert run is not None
        assert run.plan_id == data['plan_id']
        assert run.status == 'ok'
        assert run.candidate_count == 6
        assert run.verified_cal == 1530
        assert run.fallback_used is False
