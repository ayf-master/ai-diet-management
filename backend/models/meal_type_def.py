from app import db


class MealTypeDef(db.Model):
    __tablename__ = 'meal_type_def'

    type_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type_name = db.Column(db.String(20), unique=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'type_id': self.type_id,
            'type_name': self.type_name,
            'sort_order': self.sort_order,
        }
