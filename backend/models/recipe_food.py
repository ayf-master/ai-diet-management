from app import db


class RecipeFood(db.Model):
    __tablename__ = 'recipe_food'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.recipe_id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('food.food_id'), nullable=False)
    weight = db.Column(db.Float, nullable=False)

    food = db.relationship('Food', lazy='joined')

    def to_dict(self):
        return {
            'food_id': self.food_id,
            'food_name': self.food.food_name if self.food else None,
            'weight': self.weight,
            'calorie': round(self.food.nutrition.calorie * self.weight / 100, 0) if self.food and self.food.nutrition else 0,
        }
