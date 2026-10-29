"""AI 周报只负责编排，周统计来自 stats_service。"""
from datetime import date, timedelta


def test_ai_report_reuses_weekly_stats(
    client, alice_token, auth_headers, seed_ids, monkeypatch,
):
    captured = {}

    def fake_report(user_info, weekly_stats, weight_records, diseases=None):
        captured['weekly'] = weekly_stats
        captured['weights'] = weight_records
        return {'ai_comment': '测试评价', 'suggest': '测试建议', 'score': 80}

    monkeypatch.setattr('routes.ai.generate_weekly_report', fake_report)

    res = client.post(
        '/api/ai/report',
        json={'user_id': seed_ids['alice']},
        headers=auth_headers(alice_token),
    )
    assert res.status_code == 200

    weekly = captured['weekly']
    assert weekly['start'] == str(date.today() - timedelta(days=6))
    assert weekly['end'] == str(date.today())
    assert len(weekly['daily']) == 7
    assert isinstance(captured['weights'], list)

    data = res.get_json()['data']
    assert data['ai_comment'] == '测试评价'
    assert data['start_date'] == weekly['start']
