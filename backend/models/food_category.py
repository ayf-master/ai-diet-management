from app import db


class FoodCategory(db.Model):
    __tablename__ = 'food_category'

    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_name = db.Column(db.String(50), unique=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'category_id': self.category_id,
            'category_name': self.category_name,
            'sort_order': self.sort_order,
        }
