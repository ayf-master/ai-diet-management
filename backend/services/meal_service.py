"""打卡用例：创建/查询/删除饮食记录，热量交给 nutrition 纯函数。"""
from datetime import datetime

from app import db
from models import DietRecord, DietRecordDetail, MealTypeDef, Recipe
from services import nutrition
from services.errors import DomainError
from utils.auth import can_edit_owner, can_view_owner


def _num(value, default=0.0):
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def list_meal_types():
    types = MealTypeDef.query.order_by(MealTypeDef.sort_order).all()
    return [t.to_dict() for t in types]


def create_meal(data, *, user_id):
    if not isinstance(data, dict) or not data:
        raise DomainError(400, '请求数据为空')

    record = DietRecord(
        user_id=user_id,
        meal_type_id=data.get('meal_type_id', 1),
        eat_date=data.get('eat_date', datetime.now().strftime('%Y-%m-%d')),
        eat_time=data.get('eat_time'),
        note=data.get('note'),
    )

    try:
        db.session.add(record)
        db.session.flush()

        total_cal = 0
        for item in data.get('details') or []:
            recipe_id = item.get('recipe_id') if isinstance(item, dict) else None
            if not recipe_id:
                raise DomainError(400, '打卡明细缺少 recipe_id')

            recipe = db.session.get(Recipe, recipe_id)
            # 只能打卡自己可见的食谱（系统食谱或本人自建）
            if not recipe or not can_view_owner(
                recipe.user_id, user_id, False
            ):
                continue

            if 'eat_weight' in item and item.get('eat_weight') is not None:
                weight = _num(item.get('eat_weight'))
            else:
                weight = _num(recipe.total_weight) or 100

            calc = nutrition.calc_meal_item(
                recipe.total_weight,
                recipe.base_calorie,
                recipe.total_calorie,
                recipe.oil_g,
                recipe.sauce_g,
                weight,
                override_oil=item.get('oil_g'),
                override_sauce=item.get('sauce_g'),
            )
            db.session.add(DietRecordDetail(
                record_id=record.record_id,
                recipe_id=recipe_id,
                eat_weight=weight,
                single_cal=calc.single_cal,
                oil_g=calc.oil_g,
                sauce_g=calc.sauce_g,
            ))
            total_cal += calc.single_cal

        record.total_cal = total_cal
        db.session.commit()
        db.session.refresh(record)
        return record
    except Exception:
        db.session.rollback()
        raise


def list_meals(user_id, date_str=''):
    query = DietRecord.query.filter_by(user_id=user_id)
    if date_str:
        query = query.filter_by(eat_date=date_str)
    return query.order_by(DietRecord.eat_date.desc(), DietRecord.eat_time).all()


def delete_meal(record_id, *, viewer_id, viewer_is_admin=False):
    record = db.session.get(DietRecord, record_id)
    if not record:
        raise DomainError(404, '记录不存在')
    if not can_edit_owner(record.user_id, viewer_id, viewer_is_admin):
        raise DomainError(403, '无权操作该记录')

    db.session.delete(record)
    db.session.commit()
