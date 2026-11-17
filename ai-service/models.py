# AI 服务所需的全部数据表：业务表只读，AI 三张表本服务拥有并写入
from db import db


class UserGoal(db.Model):
    __tablename__ = 'user_goal'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer)
    goal = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class User(db.Model):
    __tablename__ = 'user'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    account = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(255))
    nickname = db.Column(db.String(50))
    avatar_url = db.Column(db.String(255))
    email = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.Integer)          # 0女 1男
    height = db.Column(db.Float)
    current_weight = db.Column(db.Float)
    target_weight = db.Column(db.Float)
    activity_level = db.Column(db.Integer)  # 1~4
    diet_goal = db.Column(db.String(20), default='healthy')
    custom_target_cal = db.Column(db.Integer)
    recommend_cal = db.Column(db.Integer)
    bmr = db.Column(db.Float)
    # 数据库生成列，只读
    bmi = db.Column(db.Float)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now())

    goals = db.relationship('UserGoal', lazy='joined',
                            primaryjoin='User.user_id == UserGoal.user_id',
                            foreign_keys=[UserGoal.user_id])

    def to_dict(self):
        goal_list = [g.goal for g in self.goals] if self.goals else [self.diet_goal]
        return {
            'user_id': self.user_id,
            'account': self.account,
            'nickname': self.nickname,
            'avatar_url': self.avatar_url,
            'email': self.email,
            'age': self.age,
            'gender': self.gender,
            'height': self.height,
            'current_weight': self.current_weight,
            'target_weight': self.target_weight,
            'activity_level': self.activity_level,
            'diet_goal': self.diet_goal,
            'diet_goals': goal_list,
            'custom_target_cal': self.custom_target_cal,
            'recommend_cal': self.recommend_cal,
            'bmr': self.bmr,
            'bmi': self.bmi,
            'created_at': str(self.created_at) if self.created_at else None,
        }


class Nutrition(db.Model):
    __tablename__ = 'nutrition'

    nutri_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    food_id = db.Column(db.Integer)
    calorie = db.Column(db.Integer, default=0)
    protein = db.Column(db.Float, default=0)
    fat = db.Column(db.Float, default=0)
    carbohydrate = db.Column(db.Float, default=0)
    fiber = db.Column(db.Float, default=0)
    sugar = db.Column(db.Float, default=0)
    sodium = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            'calorie': self.calorie,
            'protein': self.protein,
            'fat': self.fat,
            'carbohydrate': self.carbohydrate,
            'fiber': self.fiber,
            'sugar': self.sugar,
            'sodium': self.sodium,
        }


class Food(db.Model):
    __tablename__ = 'food'

    food_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    food_name = db.Column(db.String(100))
    category_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    unit = db.Column(db.String(20), default='100g')
    img_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    nutrition = db.relationship('Nutrition', lazy='joined',
                                primaryjoin='Food.food_id == Nutrition.food_id',
                                foreign_keys=[Nutrition.food_id], uselist=False)


class RecipeFood(db.Model):
    __tablename__ = 'recipe_food'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recipe_id = db.Column(db.Integer)
    food_id = db.Column(db.Integer)
    weight = db.Column(db.Float)

    food = db.relationship('Food', lazy='joined',
                           primaryjoin='RecipeFood.food_id == Food.food_id',
                           foreign_keys='RecipeFood.food_id')


class Recipe(db.Model):
    __tablename__ = 'recipe'

    recipe_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    recipe_name = db.Column(db.String(100))
    type = db.Column(db.String(20))
    suitable_goals = db.Column(db.String(50), default='healthy')
    intro = db.Column(db.Text)
    img_path = db.Column(db.String(255))
    cook_method = db.Column(db.String(50))
    forbid_tips = db.Column(db.Text)
    total_calorie = db.Column(db.Integer, default=0)
    added_calorie = db.Column(db.Integer, default=0)
    base_calorie = db.Column(db.Integer, default=0)
    total_weight = db.Column(db.Float, default=0)
    oil_g = db.Column(db.Float, default=0)
    sauce_g = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now())

    ingredients = db.relationship('RecipeFood', lazy='joined',
                                  primaryjoin='Recipe.recipe_id == RecipeFood.recipe_id',
                                  foreign_keys='RecipeFood.recipe_id')


class Disease(db.Model):
    __tablename__ = 'disease'

    disease_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    disease_name = db.Column(db.String(100))
    forbid_desc = db.Column(db.Text)
    forbid_keywords = db.Column(db.Text)
    forbid_rules = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class UserDisease(db.Model):
    __tablename__ = 'user_disease'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer)
    disease_id = db.Column(db.Integer)
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class DietRecord(db.Model):
    __tablename__ = 'diet_record'

    record_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer)
    meal_type_id = db.Column(db.Integer)
    eat_date = db.Column(db.Date)
    eat_time = db.Column(db.Time)
    total_cal = db.Column(db.Integer, default=0)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class WeightRecord(db.Model):
    __tablename__ = 'weight_record'

    record_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer)
    weight = db.Column(db.Float)
    body_fat_rate = db.Column(db.Float)
    measure_date = db.Column(db.Date)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class AiDietPlan(db.Model):
    __tablename__ = 'ai_diet_plan'

    plan_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    create_date = db.Column(db.Date, nullable=False)
    plan_content = db.Column(db.Text, nullable=False)
    breakfast_ids = db.Column(db.String(255))
    lunch_ids = db.Column(db.String(255))
    dinner_ids = db.Column(db.String(255))
    snack_ids = db.Column(db.String(255))
    forbid_food = db.Column(db.Text)
    total_cal = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            'plan_id': self.plan_id,
            'user_id': self.user_id,
            'create_date': str(self.create_date) if self.create_date else None,
            'plan_content': self.plan_content,
            'breakfast_ids': self.breakfast_ids,
            'lunch_ids': self.lunch_ids,
            'dinner_ids': self.dinner_ids,
            'snack_ids': self.snack_ids,
            'forbid_food': self.forbid_food,
            'total_cal': self.total_cal,
            'created_at': str(self.created_at) if self.created_at else None,
        }


class AiPlanRun(db.Model):
    # 每次可信 AI 规划的可观测指标；失败也留痕
    __tablename__ = 'ai_plan_run'

    run_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    plan_id = db.Column(db.Integer)
    status = db.Column(db.String(20), default='failed')
    model = db.Column(db.String(50))
    source = db.Column(db.String(20))           # model / mock / fallback
    candidate_count = db.Column(db.Integer, default=0)
    attempts = db.Column(db.Integer, default=0)
    parse_ok = db.Column(db.Boolean, default=False)
    schema_ok = db.Column(db.Boolean, default=False)
    invalid_id_count = db.Column(db.Integer, default=0)
    repaired_count = db.Column(db.Integer, default=0)
    danger_count = db.Column(db.Integer, default=0)
    target_cal = db.Column(db.Integer)
    verified_cal = db.Column(db.Integer)
    calorie_error_pct = db.Column(db.Float)
    protein_g = db.Column(db.Float)
    fallback_used = db.Column(db.Boolean, default=False)
    latency_ms = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            'run_id': self.run_id,
            'user_id': self.user_id,
            'plan_id': self.plan_id,
            'status': self.status,
            'model': self.model,
            'source': self.source,
            'candidate_count': self.candidate_count,
            'attempts': self.attempts,
            'parse_ok': self.parse_ok,
            'schema_ok': self.schema_ok,
            'invalid_id_count': self.invalid_id_count,
            'repaired_count': self.repaired_count,
            'danger_count': self.danger_count,
            'target_cal': self.target_cal,
            'verified_cal': self.verified_cal,
            'calorie_error_pct': self.calorie_error_pct,
            'protein_g': self.protein_g,
            'fallback_used': self.fallback_used,
            'latency_ms': self.latency_ms,
            'created_at': str(self.created_at) if self.created_at else None,
        }


class AiReport(db.Model):
    __tablename__ = 'ai_report'

    report_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_cal = db.Column(db.Integer, nullable=False)
    avg_daily_cal = db.Column(db.Integer)
    weight_diff = db.Column(db.Float, nullable=False)
    ai_comment = db.Column(db.Text, nullable=False)
    suggest = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            'report_id': self.report_id,
            'user_id': self.user_id,
            'start_date': str(self.start_date) if self.start_date else None,
            'end_date': str(self.end_date) if self.end_date else None,
            'total_cal': self.total_cal,
            'avg_daily_cal': self.avg_daily_cal,
            'weight_diff': self.weight_diff,
            'ai_comment': self.ai_comment,
            'suggest': self.suggest,
            'created_at': str(self.created_at) if self.created_at else None,
        }
