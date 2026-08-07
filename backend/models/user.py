from app import db
from sqlalchemy import FetchedValue


class User(db.Model):
    __tablename__ = 'user'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    account = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(50), nullable=False)
    avatar_url = db.Column(db.String(255))
    email = db.Column(db.String(100))
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.Integer, nullable=False)  # 0女 1男
    height = db.Column(db.Float, nullable=False)
    current_weight = db.Column(db.Float, nullable=False)
    target_weight = db.Column(db.Float, nullable=False)
    activity_level = db.Column(db.Integer, nullable=False)  # 1~4
    diet_goal = db.Column(db.String(20), nullable=False, default='healthy')
    custom_target_cal = db.Column(db.Integer)
    recommend_cal = db.Column(db.Integer, nullable=False)
    bmr = db.Column(db.Float)
    bmi = db.Column(db.Float, FetchedValue())
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    goals = db.relationship('UserGoal', backref='user', lazy='joined')

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
