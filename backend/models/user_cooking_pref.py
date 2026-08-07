from app import db


class UserCookingPref(db.Model):
    __tablename__ = 'user_cooking_pref'

    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), primary_key=True)
    cook_method = db.Column(db.String(50), primary_key=True)
    oil_per_100g = db.Column(db.Float, nullable=False, default=0)
    sauce_kcal_per_100g = db.Column(db.Float, nullable=False, default=0)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'cook_method': self.cook_method,
            'oil_per_100g': self.oil_per_100g,
            'sauce_kcal_per_100g': self.sauce_kcal_per_100g,
        }
