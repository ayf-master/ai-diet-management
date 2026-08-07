from app import db


class Food(db.Model):
    __tablename__ = 'food'

    food_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    food_name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('food_category.category_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    unit = db.Column(db.String(20), nullable=False, default='100g')
    img_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    category = db.relationship('FoodCategory', backref='foods')
    nutrition = db.relationship('Nutrition', backref='food', uselist=False,
                                 cascade='all, delete', passive_deletes=True)

    def to_dict(self):
        return {
            'food_id': self.food_id,
            'food_name': self.food_name,
            'category_id': self.category_id,
            'user_id': self.user_id,
            'category_name': self.category.category_name if self.category else None,
            'unit': self.unit,
            'img_path': self.img_path,
            'nutrition': self.nutrition.to_dict() if self.nutrition else None,
            'created_at': str(self.created_at) if self.created_at else None,
        }
