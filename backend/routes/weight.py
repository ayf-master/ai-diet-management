from datetime import date
from flask import request, jsonify
from app import db
from models import WeightRecord
from . import api


@api.route('/weight', methods=['POST'])
def record_weight():
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'msg': '请求数据为空'}), 400

    user_id = data.get('user_id')
    weight = data.get('weight')
    if not user_id or not weight:
        return jsonify({'code': 400, 'msg': 'user_id和weight不能为空'}), 400

    db.session.execute(
        db.text('CALL sp_record_weight(:uid, :weight, :body_fat, :mdate, :note)'),
        {
            'uid': user_id,
            'weight': weight,
            'body_fat': data.get('body_fat_rate'),
            'mdate': data.get('measure_date', str(date.today())),
            'note': data.get('note'),
        }
    )
    db.session.commit()

    record = WeightRecord.query.filter_by(
        user_id=user_id, weight=weight
    ).order_by(WeightRecord.created_at.desc()).first()
    return jsonify({'code': 200, 'msg': '记录成功', 'data': record.to_dict() if record else None}), 200


@api.route('/weight', methods=['GET'])
def list_weight():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'code': 400, 'msg': '缺少user_id'}), 400

    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)

    records = WeightRecord.query.filter_by(user_id=user_id)\
        .order_by(WeightRecord.measure_date.desc())\
        .limit(limit).offset(offset).all()
    return jsonify({'code': 200, 'data': [r.to_dict() for r in records]})


@api.route('/weight/latest', methods=['GET'])
def latest_weight():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'code': 400, 'msg': '缺少user_id'}), 400

    record = WeightRecord.query.filter_by(user_id=user_id)\
        .order_by(WeightRecord.measure_date.desc()).first()
    return jsonify({'code': 200, 'data': record.to_dict() if record else None})


@api.route('/weight/<int:record_id>', methods=['DELETE'])
def delete_weight(record_id):
    record = WeightRecord.query.get(record_id)
    if not record:
        return jsonify({'code': 404, 'msg': '记录不存在'}), 404

    db.session.delete(record)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '删除成功'})
