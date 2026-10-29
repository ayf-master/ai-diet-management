from flask import request, jsonify
from app import db
from models import Disease, UserDisease
from utils.auth import auth_required, ensure_owner, resolve_user_id
from . import api


@api.route('/diseases', methods=['GET'])
@auth_required
def list_diseases():
    diseases = Disease.query.order_by(Disease.disease_id).all()
    return jsonify({'code': 200, 'data': [d.to_dict() for d in diseases]})


@api.route('/user/diseases', methods=['GET'])
@auth_required
def list_user_diseases():
    user_id, err = resolve_user_id(request.args.get('user_id', type=int))
    if err:
        return err

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
@auth_required
def add_user_disease():
    data = request.get_json()
    if not data or not data.get('disease_id'):
        return jsonify({'code': 400, 'msg': 'disease_id 不能为空'}), 400

    user_id, err = resolve_user_id(data.get('user_id'))
    if err:
        return err

    existing = UserDisease.query.filter_by(
        user_id=user_id, disease_id=data['disease_id']
    ).first()
    if existing:
        return jsonify({'code': 409, 'msg': '该疾病已关联'}), 409

    record = UserDisease(
        user_id=user_id,
        disease_id=data['disease_id'],
        remark=data.get('remark'),
    )
    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return jsonify({'code': 200, 'msg': '添加成功', 'data': record.to_dict()}), 200


@api.route('/user/diseases/<int:id>', methods=['DELETE'])
@auth_required
def delete_user_disease(id):
    record = UserDisease.query.get(id)
    if not record:
        return jsonify({'code': 404, 'msg': '记录不存在'}), 404
    err = ensure_owner(record)
    if err:
        return err

    db.session.delete(record)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '删除成功'})


@api.route('/user/diseases/<int:id>', methods=['PUT'])
@auth_required
def update_user_disease(id):
    record = UserDisease.query.get(id)
    if not record:
        return jsonify({'code': 404, 'msg': '记录不存在'}), 404
    err = ensure_owner(record)
    if err:
        return err
    data = request.get_json() or {}
    if 'remark' in data:
        record.remark = data['remark'] or None
    db.session.commit()
    db.session.refresh(record)
    return jsonify({'code': 200, 'msg': '更新成功', 'data': record.to_dict()})
