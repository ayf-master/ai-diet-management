from app import db


class Nutrition(db.Model):
    __tablename__ = 'nutrition'

    nutri_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    food_id = db.Column(db.Integer, db.ForeignKey('food.food_id'), unique=True, nullable=False)
    calorie = db.Column(db.Integer, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    carbohydrate = db.Column(db.Float, nullable=False)
    fiber = db.Column(db.Float, nullable=False, default=0)
    sugar = db.Column(db.Float, nullable=False, default=0)
    sodium = db.Column(db.Float, nullable=False, default=0)
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
