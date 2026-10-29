"""pytest 配置：测试库独立，跑完即删。"""
import os
import sys

# 必须在导入 app 之前设置，Config 在 import 时读取环境变量
os.environ['DB_NAME'] = 'diet_management_test'
os.environ.setdefault('SECRET_KEY', 'test-secret-key-at-least-32-bytes-long!!')

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

import pymysql
import pytest
from sqlalchemy import make_url, text
from werkzeug.security import generate_password_hash

from app import create_app, db
from models import (
    Admin, AiDietPlan, CookingMethod, DietRecord, Food, FoodCategory,
    MealTypeDef, Nutrition, Recipe, RecipeFood, User, WeightRecord,
)
from services.planning.view import RECIPE_NUTRITION_VIEW_SQL


def _server_connection(uri, database=None):
    url = make_url(uri)
    return pymysql.connect(
        host=url.host,
        user=url.username,
        password=url.password,
        port=url.port or 3306,
        database=database,
        autocommit=True,
    )


@pytest.fixture(scope='session')
def app():
    application = create_app()
    uri = application.config['SQLALCHEMY_DATABASE_URI']
    conn = _server_connection(uri)
    with conn.cursor() as cur:
        cur.execute('DROP DATABASE IF EXISTS diet_management_test')
        cur.execute('CREATE DATABASE diet_management_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    conn.close()

    with application.app_context():
        db.create_all()
        db.session.execute(text(RECIPE_NUTRITION_VIEW_SQL))
        db.session.commit()
        _seed()
    _create_procedures(uri, 'diet_management_test')

    yield application

    with application.app_context():
        db.session.remove()
        db.drop_all()
    conn = _server_connection(uri)
    with conn.cursor() as cur:
        cur.execute('DROP DATABASE IF EXISTS diet_management_test')
    conn.close()


def _seed():
    """最小数据集：两个用户、一个管理员、系统/个人食材、一个系统食谱、一条打卡。"""
    u1 = User(
        account='alice', password=generate_password_hash('pass1234'), nickname='Alice',
        email='alice@example.com', age=25, gender=0, height=165, current_weight=60,
        target_weight=55, activity_level=2, diet_goal='lose_weight', recommend_cal=1500,
    )
    u2 = User(
        account='bob', password=generate_password_hash('pass1234'), nickname='Bob',
        email='bob@example.com', age=28, gender=1, height=178, current_weight=80,
        target_weight=72, activity_level=3, diet_goal='lose_weight', recommend_cal=2000,
    )
    admin = Admin(
        account='admin', password=generate_password_hash('admin1234'), nickname='管理员',
    )
    cat = FoodCategory(category_name='测试分类', sort_order=1)
    db.session.add_all([u1, u2, admin, cat])
    db.session.flush()

    system_food = Food(food_name='系统鸡胸肉', category_id=cat.category_id, unit='100g')
    alice_food = Food(food_name='Alice 的燕麦', category_id=cat.category_id, unit='100g', user_id=u1.user_id)
    bob_food = Food(food_name='Bob 的香蕉', category_id=cat.category_id, unit='100g', user_id=u2.user_id)
    db.session.add_all([system_food, alice_food, bob_food])
    db.session.flush()

    for food, cal in ((system_food, 133), (alice_food, 389), (bob_food, 89)):
        db.session.add(Nutrition(
            food_id=food.food_id, calorie=cal, protein=20, fat=2,
            carbohydrate=3, fiber=1, sugar=1, sodium=50,
        ))

    breakfast = MealTypeDef(type_name='早餐', sort_order=1)
    db.session.add(breakfast)
    db.session.add_all([
        CookingMethod(cook_method='煮', oil_per_100g=0, sauce_kcal_per_100g=0),
        CookingMethod(cook_method='炒', oil_per_100g=5, sauce_kcal_per_100g=10),
    ])
    db.session.flush()

    system_recipe = Recipe(
        admin_id=admin.admin_id, recipe_name='系统食谱', type='早餐',
        suitable_goals='healthy', cook_method='煮', total_weight=100,
        base_calorie=133, added_calorie=0, total_calorie=133,
    )
    alice_recipe = Recipe(
        user_id=u1.user_id, recipe_name='Alice 食谱', type='早餐',
        suitable_goals='healthy', cook_method='煮', total_weight=50,
        base_calorie=100, added_calorie=0, total_calorie=100,
    )
    system_lunch = Recipe(
        admin_id=admin.admin_id, recipe_name='系统午餐', type='午餐',
        suitable_goals='healthy,lose_weight', cook_method='煮', total_weight=300,
        base_calorie=399, added_calorie=0, total_calorie=399,
    )
    alice_lunch = Recipe(
        user_id=u1.user_id, recipe_name='Alice 午餐', type='午餐',
        suitable_goals='lose_weight', cook_method='煮', total_weight=200,
        base_calorie=522, added_calorie=0, total_calorie=522,
    )
    system_dinner = Recipe(
        admin_id=admin.admin_id, recipe_name='系统晚餐', type='晚餐',
        suitable_goals='healthy,lose_weight', cook_method='煮', total_weight=400,
        base_calorie=532, added_calorie=0, total_calorie=532,
    )
    system_snack = Recipe(
        admin_id=admin.admin_id, recipe_name='系统加餐', type='加餐',
        suitable_goals='healthy', cook_method='煮', total_weight=100,
        base_calorie=133, added_calorie=0, total_calorie=133,
    )
    db.session.add_all([
        system_recipe, alice_recipe, system_lunch, alice_lunch,
        system_dinner, system_snack,
    ])
    db.session.flush()
    db.session.add(RecipeFood(recipe_id=system_recipe.recipe_id, food_id=system_food.food_id, weight=100))
    db.session.add(RecipeFood(recipe_id=system_lunch.recipe_id, food_id=system_food.food_id, weight=300))
    db.session.add(RecipeFood(recipe_id=alice_lunch.recipe_id, food_id=alice_food.food_id, weight=100))
    db.session.add(RecipeFood(recipe_id=alice_lunch.recipe_id, food_id=system_food.food_id, weight=100))
    db.session.add(RecipeFood(recipe_id=system_dinner.recipe_id, food_id=system_food.food_id, weight=400))
    db.session.add(RecipeFood(recipe_id=system_snack.recipe_id, food_id=system_food.food_id, weight=100))

    db.session.add(DietRecord(
        user_id=u1.user_id, meal_type_id=breakfast.type_id,
        eat_date='2026-08-01', total_cal=133,
    ))
    db.session.add(DietRecord(
        user_id=u2.user_id, meal_type_id=breakfast.type_id,
        eat_date='2026-08-01', total_cal=100,
    ))
    db.session.add(WeightRecord(
        user_id=u2.user_id, weight=80, measure_date='2026-08-01',
    ))
    db.session.add(AiDietPlan(
        user_id=u2.user_id, create_date='2026-08-01',
        plan_content='{"meals": []}', total_cal=1800,
    ))
    db.session.commit()


@pytest.fixture()
def seed_ids(app):
    """把种子数据的真实主键取出来，避免测试里硬编码 id。"""
    with app.app_context():
        alice = User.query.filter_by(account='alice').first()
        bob = User.query.filter_by(account='bob').first()
        return {
            'alice': alice.user_id,
            'bob': bob.user_id,
            'breakfast': MealTypeDef.query.filter_by(type_name='早餐').first().type_id,
            'system_food': Food.query.filter_by(food_name='系统鸡胸肉').first().food_id,
            'alice_food': Food.query.filter_by(food_name='Alice 的燕麦').first().food_id,
            'bob_food': Food.query.filter_by(food_name='Bob 的香蕉').first().food_id,
            'alice_meal': DietRecord.query.filter_by(user_id=alice.user_id).first().record_id,
            'bob_meal': DietRecord.query.filter_by(user_id=bob.user_id).first().record_id,
            'bob_weight': WeightRecord.query.filter_by(user_id=bob.user_id).first().record_id,
            'bob_plan': AiDietPlan.query.filter_by(user_id=bob.user_id).first().plan_id,
            'system_recipe': Recipe.query.filter_by(recipe_name='系统食谱').first().recipe_id,
            'alice_recipe': Recipe.query.filter_by(recipe_name='Alice 食谱').first().recipe_id,
            'system_lunch': Recipe.query.filter_by(recipe_name='系统午餐').first().recipe_id,
            'alice_lunch': Recipe.query.filter_by(recipe_name='Alice 午餐').first().recipe_id,
            'system_dinner': Recipe.query.filter_by(recipe_name='系统晚餐').first().recipe_id,
            'system_snack': Recipe.query.filter_by(recipe_name='系统加餐').first().recipe_id,
        }


def _create_procedures(uri, database):
    """测试库只需要被接口调用到的两个存储过程，保持与生产库行为一致。"""
    conn = _server_connection(uri, database)
    with conn.cursor() as cur:
        cur.execute('DROP PROCEDURE IF EXISTS sp_recommend_daily_cal')
        cur.execute("""
            CREATE PROCEDURE sp_recommend_daily_cal(IN p_uid INT)
            BEGIN
                UPDATE user SET recommend_cal = 1500 WHERE user_id = p_uid;
            END
        """)
        cur.execute('DROP PROCEDURE IF EXISTS sp_record_weight')
        cur.execute("""
            CREATE PROCEDURE sp_record_weight(
                IN p_uid INT, IN p_weight FLOAT, IN p_body_fat FLOAT,
                IN p_mdate DATE, IN p_note TEXT
            )
            BEGIN
                INSERT INTO weight_record (user_id, weight, body_fat_rate, measure_date, note)
                VALUES (p_uid, p_weight, p_body_fat, p_mdate, p_note);
            END
        """)
    conn.close()


@pytest.fixture()
def client(app):
    return app.test_client()


def _login(client, account, password):
    res = client.post('/api/login', json={'account': account, 'password': password})
    assert res.status_code == 200, res.get_json()
    return res.get_json()['access_token']


@pytest.fixture()
def alice_token(client):
    return _login(client, 'alice', 'pass1234')


@pytest.fixture()
def bob_token(client):
    return _login(client, 'bob', 'pass1234')


@pytest.fixture()
def admin_token(client):
    res = client.post('/api/admin/login', json={'account': 'admin', 'password': 'admin1234'})
    assert res.status_code == 200, res.get_json()
    return res.get_json()['access_token']


@pytest.fixture()
def auth_headers():
    def make(token):
        return {'Authorization': f'Bearer {token}'}
    return make
