from flask import request, jsonify
from app import db
from models import Disease, UserDisease
from . import api


@api.route('/diseases', methods=['GET'])
def list_diseases():
    diseases = Disease.query.order_by(Disease.disease_id).all()
    return jsonify({'code': 200, 'data': [d.to_dict() for d in diseases]})


@api.route('/user/diseases', methods=['GET'])
def list_user_diseases():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'code': 400, 'msg': '缺少user_id'}), 400

    records = UserDisease.query.filter_by(user_id=user_id).all()
    result = []
    for r in records:
        d = r.to_dict()
        disease = Disease.query.get(r.disease_id)
        d['disease_name'] = disease.disease_name if disease else None
        d['forbid_desc'] = disease.forbid_desc if disease else None
        result.append(d)
    return jsonify({'code': 200, 'data': result})


@api.route('/user/diseases', methods=['POST'])
def add_user_disease():
    data = request.get_json()
    if not data or not data.get('user_id') or not data.get('disease_id'):
        return jsonify({'code': 400, 'msg': 'user_id和disease_id不能为空'}), 400

    existing = UserDisease.query.filter_by(
        user_id=data['user_id'], disease_id=data['disease_id']
    ).first()
    if existing:
        return jsonify({'code': 409, 'msg': '该疾病已关联'}), 409

    record = UserDisease(
        user_id=data['user_id'],
        disease_id=data['disease_id'],
        remark=data.get('remark'),
    )
    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return jsonify({'code': 200, 'msg': '添加成功', 'data': record.to_dict()}), 200


@api.route('/user/diseases/<int:id>', methods=['DELETE'])
def delete_user_disease(id):
    record = UserDisease.query.get(id)
    if not record:
        return jsonify({'code': 404, 'msg': '记录不存在'}), 404

    db.session.delete(record)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '删除成功'})


@api.route('/user/diseases/<int:id>', methods=['PUT'])
def update_user_disease(id):
    record = UserDisease.query.get(id)
    if not record:
        return jsonify({'code': 404, 'msg': '记录不存在'}), 404
    data = request.get_json() or {}
    if 'remark' in data:
        record.remark = data['remark'] or None
    db.session.commit()
    db.session.refresh(record)
    return jsonify({'code': 200, 'msg': '更新成功', 'data': record.to_dict()})
