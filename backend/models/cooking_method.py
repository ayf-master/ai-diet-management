from app import db


class CookingMethod(db.Model):
    """烹饪方式 → 热量附加系数表

    同一种食材经不同烹饪方式处理后，热量差异主要来自：
    1. 食用油（oil_per_100g，单位 g/100g 食材，×9 得油热量）
    2. 典型酱料/糖（sauce_kcal_per_100g，单位 kcal/100g 食材）
    系数均为估算值，可由管理员在后台维护。
    """

    __tablename__ = 'cooking_method'

    cook_method = db.Column(db.String(50), primary_key=True)
    oil_per_100g = db.Column(db.Float, nullable=False, default=0)
    sauce_kcal_per_100g = db.Column(db.Float, nullable=False, default=0)
    description = db.Column(db.Text)

    def to_dict(self):
        return {
            'cook_method': self.cook_method,
            'oil_per_100g': self.oil_per_100g,
            'sauce_kcal_per_100g': self.sauce_kcal_per_100g,
            'description': self.description,
        }
