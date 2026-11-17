"""阶段 7.1：工具契约、参数校验、身份注入与可见性。"""
from app import db
from models import User
from services.agent.tools import (
    ToolRegistry, ToolResult, ToolSpec, UserProfileArgs, execute_tool,
)


def test_unknown_tool_returns_observation_not_exception(app, seed_ids):
    with app.app_context():
        alice = db.session.get(User, seed_ids['alice'])
        result = execute_tool('delete_everything', {}, alice)
        assert result.ok is False
        assert result.error_code == 'unknown_tool'


def test_invalid_arguments_are_rejected(app, seed_ids):
    with app.app_context():
        alice = db.session.get(User, seed_ids['alice'])
        result = execute_tool('search_recipes', {'meal_type': 'brunch'}, alice)
        assert result.ok is False
        assert result.error_code == 'invalid_arguments'
        assert 'meal_type' in result.message


def test_model_cannot_inject_user_id(app, seed_ids):
    with app.app_context():
        alice = db.session.get(User, seed_ids['alice'])
        result = execute_tool('get_user_profile', {'user_id': seed_ids['bob']}, alice)
        assert result.ok is False
        assert result.error_code == 'invalid_arguments'
        assert 'user_id' in result.message


def test_get_user_profile_returns_current_user_only(app, seed_ids):
    with app.app_context():
        alice = db.session.get(User, seed_ids['alice'])
        result = execute_tool('get_user_profile', {}, alice)
        assert result.ok is True
        assert result.data['user_id'] == seed_ids['alice']
        assert 'password' not in result.data
        assert 'email' not in result.data
        assert result.data['recommend_cal'] == alice.recommend_cal


def test_search_recipes_respects_visibility(app, seed_ids):
    with app.app_context():
        alice = db.session.get(User, seed_ids['alice'])
        result = execute_tool(
            'search_recipes',
            {'meal_type': 'lunch', 'goal': 'lose_weight', 'limit': 8},
            alice,
        )
        assert result.ok is True
        ids = {c['recipe_id'] for c in result.data['candidates']}
        assert seed_ids['system_lunch'] in ids
        assert seed_ids['alice_lunch'] in ids

        bob = db.session.get(User, seed_ids['bob'])
        bob_result = execute_tool(
            'search_recipes',
            {'meal_type': 'lunch', 'goal': 'healthy', 'limit': 8},
            bob,
        )
        bob_ids = {c['recipe_id'] for c in bob_result.data['candidates']}
        assert seed_ids['system_lunch'] in bob_ids
        assert seed_ids['alice_lunch'] not in bob_ids


def test_calculate_nutrition_uses_database_view(app, seed_ids):
    with app.app_context():
        alice = db.session.get(User, seed_ids['alice'])
        result = execute_tool(
            'calculate_recipe_nutrition',
            {'recipe_id': seed_ids['system_lunch'], 'weight_g': 300},
            alice,
        )
        assert result.ok is True
        assert result.data['calorie'] == 399.0
        assert result.data['protein_g'] == 60.0
        assert result.data['fat_g'] == 6.0


def test_calculate_nutrition_hides_other_users_recipe(app, seed_ids):
    with app.app_context():
        bob = db.session.get(User, seed_ids['bob'])
        result = execute_tool(
            'calculate_recipe_nutrition',
            {'recipe_id': seed_ids['alice_lunch'], 'weight_g': 200},
            bob,
        )
        assert result.ok is False
        assert result.error_code == 'not_found'


def test_weight_out_of_range_is_rejected(app, seed_ids):
    with app.app_context():
        alice = db.session.get(User, seed_ids['alice'])
        result = execute_tool(
            'calculate_recipe_nutrition',
            {'recipe_id': seed_ids['system_lunch'], 'weight_g': -1},
            alice,
        )
        assert result.ok is False
        assert result.error_code == 'invalid_arguments'


def test_calculate_nutrition_accepts_recipe_name(app, seed_ids):
    with app.app_context():
        alice = db.session.get(User, seed_ids['alice'])
        result = execute_tool(
            'calculate_recipe_nutrition',
            {'recipe_name': '系统午餐', 'weight_g': 300},
            alice,
        )
        assert result.ok is True
        assert result.data['recipe_id'] == seed_ids['system_lunch']
        assert result.data['calorie'] == 399.0


def test_calculate_nutrition_requires_exactly_one_identifier(app, seed_ids):
    with app.app_context():
        alice = db.session.get(User, seed_ids['alice'])
        for args in (
            {'weight_g': 300},
            {'recipe_id': seed_ids['system_lunch'], 'recipe_name': '系统午餐', 'weight_g': 300},
        ):
            result = execute_tool('calculate_recipe_nutrition', args, alice)
            assert result.ok is False
            assert result.error_code == 'invalid_arguments'


def test_calculate_nutrition_by_name_hides_other_users_recipe(app, seed_ids):
    with app.app_context():
        bob = db.session.get(User, seed_ids['bob'])
        result = execute_tool(
            'calculate_recipe_nutrition',
            {'recipe_name': 'Alice 午餐', 'weight_g': 200},
            bob,
        )
        assert result.ok is False
        assert result.error_code == 'not_found'


def test_handler_exception_becomes_tool_failed(app, seed_ids):
    def boom(args, user):
        raise RuntimeError('database down')

    registry = ToolRegistry()
    registry.register(ToolSpec(
        name='boom',
        description='test only',
        args_model=UserProfileArgs,
        handler=boom,
    ))
    with app.app_context():
        alice = db.session.get(User, seed_ids['alice'])
        result = registry.execute('boom', {}, alice)
        assert result.ok is False
        assert result.error_code == 'tool_failed'
        assert 'database down' not in result.message
