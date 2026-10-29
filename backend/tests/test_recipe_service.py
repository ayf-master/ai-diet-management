"""recipe_service 单测：直接调用用例层，验证事务、重算与归属。"""
import uuid

import pytest

from app import db
from models import Recipe
from services import recipe_service
from services.errors import DomainError


def _payload(name=None, **overrides):
    data = {
        'recipe_name': name or f'测试食谱-{uuid.uuid4().hex[:6]}',
        'type': '午餐',
        'suitable_goals': 'healthy',
        'cook_method': '煮',
        'ingredients': [],
    }
    data.update(overrides)
    return data


def test_create_recipe_computes_totals(app, seed_ids):
    with app.app_context():
        recipe = recipe_service.create_recipe(
            _payload(
                ingredients=[
                    {'food_id': seed_ids['system_food'], 'weight': 100},
                    {'food_id': seed_ids['alice_food'], 'weight': 50},
                ],
                oil_g=10,
                sauce_g=5,
            ),
            owner_id=seed_ids['alice'],
            admin_id=None,
        )
        assert recipe.user_id == seed_ids['alice']
        assert recipe.total_weight == 150
        assert recipe.base_calorie == 328
        assert recipe.added_calorie == 110
        assert recipe.total_calorie == 438
        assert len(recipe.ingredients) == 2


def test_create_duplicate_recipe_raises_409(app, seed_ids):
    name = f'重名食谱-{uuid.uuid4().hex[:6]}'
    with app.app_context():
        recipe_service.create_recipe(_payload(name), owner_id=seed_ids['alice'], admin_id=None)
        with pytest.raises(DomainError) as exc:
            recipe_service.create_recipe(_payload(name), owner_id=seed_ids['alice'], admin_id=None)
        assert exc.value.code == 409


def test_update_ingredients_recomputes_totals(app, seed_ids):
    with app.app_context():
        recipe = recipe_service.create_recipe(
            _payload(ingredients=[{'food_id': seed_ids['system_food'], 'weight': 100}]),
            owner_id=seed_ids['alice'],
            admin_id=None,
        )
        updated = recipe_service.update_recipe(
            recipe.recipe_id,
            {
                'ingredients': [{'food_id': seed_ids['alice_food'], 'weight': 100}],
                'cook_method': '炒',
            },
            viewer_id=seed_ids['alice'],
            viewer_is_admin=False,
        )
        assert updated.total_weight == 100
        assert updated.base_calorie == 389
        assert updated.added_calorie == 55      # 5g 油×9 + 10kcal 酱
        assert updated.total_calorie == 444


def test_update_only_cook_method_recomputes_from_existing_ingredients(app, seed_ids):
    with app.app_context():
        recipe = recipe_service.create_recipe(
            _payload(
                cook_method='煮',
                ingredients=[{'food_id': seed_ids['system_food'], 'weight': 100}],
            ),
            owner_id=seed_ids['alice'],
            admin_id=None,
        )
        updated = recipe_service.update_recipe(
            recipe.recipe_id,
            {'cook_method': '炒'},
            viewer_id=seed_ids['alice'],
            viewer_is_admin=False,
        )
        assert updated.total_weight == 100
        assert updated.base_calorie == 133
        assert updated.added_calorie == 55
        assert updated.total_calorie == 188


def test_update_to_duplicate_name_raises_409(app, seed_ids):
    with app.app_context():
        first = recipe_service.create_recipe(_payload(), owner_id=seed_ids['alice'], admin_id=None)
        second = recipe_service.create_recipe(_payload(), owner_id=seed_ids['alice'], admin_id=None)
        with pytest.raises(DomainError) as exc:
            recipe_service.update_recipe(
                second.recipe_id,
                {'recipe_name': first.recipe_name},
                viewer_id=seed_ids['alice'],
                viewer_is_admin=False,
            )
        assert exc.value.code == 409


def test_delete_recipe_removes_ingredients(app, seed_ids):
    with app.app_context():
        recipe = recipe_service.create_recipe(
            _payload(ingredients=[{'food_id': seed_ids['system_food'], 'weight': 50}]),
            owner_id=seed_ids['alice'],
            admin_id=None,
        )
        recipe_id = recipe.recipe_id

        recipe_service.delete_recipe(
            recipe_id, viewer_id=seed_ids['alice'], viewer_is_admin=False,
        )
        assert db.session.get(Recipe, recipe_id) is None


def test_system_recipe_is_editable_only_by_admin(app, seed_ids):
    with app.app_context():
        with pytest.raises(DomainError) as exc:
            recipe_service.get_editable_recipe(
                seed_ids['system_recipe'], seed_ids['alice'], False,
            )
        assert exc.value.code == 403

        recipe = recipe_service.get_editable_recipe(
            seed_ids['system_recipe'], seed_ids['alice'], True,
        )
        assert recipe.user_id is None


def test_other_users_recipe_is_not_visible(app, seed_ids):
    with app.app_context():
        with pytest.raises(DomainError) as exc:
            recipe_service.get_recipe_payload(
                seed_ids['alice_recipe'],
                viewer_id=seed_ids['bob'],
                viewer_is_admin=False,
            )
        assert exc.value.code == 404
