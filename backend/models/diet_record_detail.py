from app import db


class DietRecordDetail(db.Model):
    __tablename__ = 'diet_record_detail'

    detail_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    record_id = db.Column(db.Integer, db.ForeignKey('diet_record.record_id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.recipe_id'), nullable=False)
    eat_weight = db.Column(db.Float, nullable=False)
    single_cal = db.Column(db.Integer, nullable=False, default=0)
    oil_g = db.Column(db.Float, nullable=False, default=0)
    sauce_g = db.Column(db.Float, nullable=False, default=0)

    recipe = db.relationship('Recipe', lazy='joined')

    def to_dict(self):
        return {
            'detail_id': self.detail_id,
            'recipe_id': self.recipe_id,
            'recipe_name': self.recipe.recipe_name if self.recipe else None,
            'eat_weight': self.eat_weight,
            'single_cal': self.single_cal,
            'oil_g': self.oil_g,
            'sauce_g': self.sauce_g,
        }
