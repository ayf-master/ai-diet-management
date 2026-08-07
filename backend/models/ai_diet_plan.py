from app import db


class AiDietPlan(db.Model):
    __tablename__ = 'ai_diet_plan'

    plan_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
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
