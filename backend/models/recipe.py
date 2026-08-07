from app import db


class Recipe(db.Model):
    __tablename__ = 'recipe'

    recipe_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.admin_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    recipe_name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    suitable_goals = db.Column(db.String(50), nullable=False, default='healthy')
    intro = db.Column(db.Text)
    img_path = db.Column(db.String(255))
    cook_method = db.Column(db.String(50), nullable=False)
    forbid_tips = db.Column(db.Text)
    total_calorie = db.Column(db.Integer, nullable=False, default=0)
    added_calorie = db.Column(db.Integer, nullable=False, default=0)
    base_calorie = db.Column(db.Integer, nullable=False, default=0)
    total_weight = db.Column(db.Float, nullable=False, default=0)
    oil_g = db.Column(db.Float, nullable=False, default=0)
    sauce_g = db.Column(db.Float, nullable=False, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    ingredients = db.relationship('RecipeFood', backref='recipe', lazy='joined')

    def to_dict(self):
        return {
            'recipe_id': self.recipe_id,
            'recipe_name': self.recipe_name,
            'type': self.type,
            'suitable_goals': self.suitable_goals,
            'intro': self.intro,
            'cook_method': self.cook_method,
            'forbid_tips': self.forbid_tips,
            'total_calorie': self.total_calorie,
            'added_calorie': self.added_calorie,
            'base_calorie': self.base_calorie,
            'total_weight': self.total_weight,
            'oil_g': self.oil_g,
            'sauce_g': self.sauce_g,
            'admin_id': self.admin_id,
            'user_id': self.user_id,
            'ingredients': [i.to_dict() for i in self.ingredients],
            'created_at': str(self.created_at) if self.created_at else None,
        }
