"""SQL 候选召回：可见性、餐次、营养真值。"""
from services.planning.candidates import candidate_count, recall_candidates


def test_recall_returns_visible_candidates_by_meal(app, seed_ids):
    with app.app_context():
        from models import User
        alice = User.query.get(seed_ids['alice'])
        candidates = recall_candidates(alice, disease_rules=[])

        assert [c['recipe_id'] for c in candidates['breakfast']] == [
            seed_ids['system_recipe'], seed_ids['alice_recipe'],
        ]
        assert {c['recipe_id'] for c in candidates['lunch']} == {
            seed_ids['system_lunch'], seed_ids['alice_lunch'],
        }
        assert [c['recipe_id'] for c in candidates['dinner']] == [seed_ids['system_dinner']]
        assert [c['recipe_id'] for c in candidates['snack']] == [seed_ids['system_snack']]
        assert candidate_count(candidates) == 6

        lunch = next(c for c in candidates['lunch'] if c['recipe_id'] == seed_ids['system_lunch'])
        assert lunch['recipe_name'] == '系统午餐'
        assert lunch['total_calorie'] == 399
        assert lunch['protein_g'] > 0
        assert lunch['calorie_per_100g'] == 133


def test_recall_excludes_other_users_recipe(app, seed_ids):
    with app.app_context():
        from models import User
        bob = User.query.get(seed_ids['bob'])
        candidates = recall_candidates(bob, disease_rules=[])

        all_ids = [c['recipe_id'] for items in candidates.values() for c in items]
        assert seed_ids['alice_recipe'] not in all_ids
        assert seed_ids['alice_lunch'] not in all_ids
        assert seed_ids['system_lunch'] in all_ids
