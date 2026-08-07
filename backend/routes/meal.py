from datetime import datetime, timedelta
from flask import request, jsonify
from app import db
from models import DietRecord, DietRecordDetail, Recipe, MealTypeDef
from . import api


@api.route('/meal-types', methods=['GET'])
def list_meal_types():
    types = MealTypeDef.query.order_by(MealTypeDef.sort_order).all()
    return jsonify({'code': 200, 'data': [t.to_dict() for t in types]})


@api.route('/meals', methods=['POST'])
def create_meal():
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'msg': '请求数据为空'}), 400

    record = DietRecord(
        user_id=data['user_id'],
        meal_type_id=data.get('meal_type_id', 1),
        eat_date=data.get('eat_date', datetime.now().strftime('%Y-%m-%d')),
        eat_time=data.get('eat_time'),
        note=data.get('note'),
    )
    db.session.add(record)
    db.session.flush()

    total_cal = 0
    for item in data.get('details', []):
        recipe = Recipe.query.get(item['recipe_id'])
        if not recipe:
            continue
        weight = item.get('eat_weight', recipe.total_weight or 100)

        # 油/糖用量：优先用打卡时填的覆盖值；否则按 recipe 标准用量乘份量比缩放；否则为 0
        override_oil = item.get('oil_g')
        override_sauce = item.get('sauce_g')
        has_override = override_oil is not None and override_sauce is not None
        if has_override and (override_oil or override_sauce):
            oil_g, sauce_g = override_oil or 0, override_sauce or 0
        elif recipe.oil_g or recipe.sauce_g:
            scale = weight / (recipe.total_weight or weight)
            oil_g = (recipe.oil_g or 0) * scale
            sauce_g = (recipe.sauce_g or 0) * scale
        else:
            oil_g = sauce_g = 0

        base_part = (recipe.base_calorie or 0) * weight / (recipe.total_weight or 100)
        if (has_override and (override_oil or override_sauce)) or recipe.oil_g or recipe.sauce_g:
            # 有显式克数（食谱自带或当天覆盖）：按组分算
            cal = round(base_part + oil_g * 9 + sauce_g * 4)
        else:
            # 仅有烹饪方式系数（无显式克数）：沿用食谱总热量按份量缩放
            cal = round(recipe.total_calorie * weight / (recipe.total_weight or 100))

        detail = DietRecordDetail(
            record_id=record.record_id,
            recipe_id=item['recipe_id'],
            eat_weight=weight,
            single_cal=cal,
            oil_g=round(oil_g, 2),
            sauce_g=round(sauce_g, 2),
        )
        db.session.add(detail)
        total_cal += cal

    record.total_cal = total_cal
    db.session.commit()
    db.session.refresh(record)
    return jsonify({'code': 200, 'msg': '打卡成功', 'data': record.to_dict()}), 200


@api.route('/meals', methods=['GET'])
def list_meals():
    user_id = request.args.get('user_id', type=int)
    date_str = request.args.get('date', '')

    query = DietRecord.query
    if user_id:
        query = query.filter_by(user_id=user_id)
    if date_str:
        query = query.filter_by(eat_date=date_str)

    records = query.order_by(DietRecord.eat_date.desc(), DietRecord.eat_time).all()
    return jsonify({'code': 200, 'data': [r.to_dict() for r in records]})


@api.route('/meals/<int:record_id>', methods=['DELETE'])
def delete_meal(record_id):
    record = DietRecord.query.get(record_id)
    if not record:
        return jsonify({'code': 404, 'msg': '记录不存在'}), 404

    db.session.delete(record)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '删除成功'})


@api.route('/stats/daily', methods=['GET'])
def daily_stats():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'code': 400, 'msg': '缺少user_id'}), 400
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))

    records = DietRecord.query.filter_by(user_id=user_id, eat_date=date_str).all()
    total = sum(r.total_cal for r in records)
    meals = [{'meal_type': r.meal_type.type_name, 'cal': r.total_cal} for r in records]

    return jsonify({
        'code': 200,
        'data': {
            'date': date_str,
            'total_cal': total,
            'meal_count': len(records),
            'meals': meals,
        }
    })


@api.route('/stats/weekly', methods=['GET'])
def weekly_stats():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'code': 400, 'msg': '缺少user_id'}), 400
    end = datetime.now().date()
    start = end - timedelta(days=6)

    records = DietRecord.query.filter(
        DietRecord.user_id == user_id,
        DietRecord.eat_date.between(start, end)
    ).order_by(DietRecord.eat_date).all()

    daily_data = {}
    for r in records:
        day = str(r.eat_date)
        if day not in daily_data:
            daily_data[day] = 0
        daily_data[day] += r.total_cal

    week = [(start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    data = [{'date': d, 'cal': daily_data.get(d, 0)} for d in week]

    return jsonify({
        'code': 200,
        'data': {
            'start': str(start),
            'end': str(end),
            'total_cal': sum(r.total_cal for r in records),
            'daily': data,
        }
    })
