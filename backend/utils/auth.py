"""JWT 鉴权与资源归属校验。

设计要点：
- token 里只放身份（user_id 或 admin_id）和角色，不放昵称等可变信息；
- 所有“按 user_id 查/改”的接口都必须过 ensure_self / resolve_user_id；
- 系统资源（food.user_id / recipe.user_id 为空）只有管理员能改。
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)


def issue_token(subject_id, role='user', admin_id=None):
    """签发访问令牌：用户身份=user_id，管理员身份=admin_id。"""
    claims = {'role': role}
    if admin_id is not None:
        claims['admin_id'] = int(admin_id)
    return create_access_token(identity=str(subject_id), additional_claims=claims)


def current_user_id():
    try:
        return int(get_jwt_identity())
    except (TypeError, ValueError):
        return None


def current_role():
    return get_jwt().get('role', 'user')


def current_admin_id():
    return get_jwt().get('admin_id')


def is_admin():
    return current_role() == 'admin'


def auth_required(fn):
    """要求已登录；未登录/令牌无效统一返回 401 JSON。"""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        if current_user_id() is None:
            return jsonify({'code': 401, 'msg': '登录状态无效'}), 401
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    """要求管理员角色。"""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        if not is_admin():
            return jsonify({'code': 403, 'msg': '需要管理员权限'}), 403
        return fn(*args, **kwargs)
    return wrapper


def forbidden(msg='无权访问该资源'):
    return jsonify({'code': 403, 'msg': msg}), 403


def ensure_self(raw_user_id):
    """校验目标用户就是当前登录用户；管理员放行。

    返回 None 表示通过，否则返回 Flask 响应元组。
    """
    if raw_user_id is None:
        return None
    try:
        uid = int(raw_user_id)
    except (TypeError, ValueError):
        return jsonify({'code': 400, 'msg': 'user_id 参数无效'}), 400
    if is_admin() or uid == current_user_id():
        return None
    return forbidden('无权访问其他用户的数据')


def resolve_user_id(raw_user_id, required=True):
    """解析要操作的用户：普通用户默认自己，管理员必须显式指定。

    返回 (user_id, error)；error 非空时直接 return error。
    """
    if raw_user_id is not None:
        err = ensure_self(raw_user_id)
        if err:
            return None, err
        return int(raw_user_id), None
    if is_admin():
        if required:
            return None, (jsonify({'code': 400, 'msg': '管理员操作需指定 user_id'}), 400)
        return None, None
    return current_user_id(), None


def can_view_owner(owner_id, viewer_id, as_admin=False):
    """纯函数版可见性判断：系统资源所有人可见，个人资源仅本人/管理员。"""
    if owner_id is None:
        return True
    if as_admin:
        return True
    return viewer_id is not None and int(owner_id) == int(viewer_id)


def can_edit_owner(owner_id, viewer_id, as_admin=False):
    """纯函数版可修改判断：系统资源仅管理员，个人资源仅本人/管理员。"""
    if owner_id is None:
        return bool(as_admin)
    if as_admin:
        return True
    return viewer_id is not None and int(owner_id) == int(viewer_id)


def visible(obj, owner_field='user_id'):
    """系统资源所有人可见；个人资源仅本人和管理员可见。"""
    return can_view_owner(
        getattr(obj, owner_field, None), current_user_id(), is_admin()
    )


def ensure_owner(obj, owner_field='user_id'):
    """校验资源可修改：系统资源仅管理员，个人资源仅本人。"""
    owner_id = getattr(obj, owner_field, None)
    if can_edit_owner(owner_id, current_user_id(), is_admin()):
        return None
    if owner_id is None:
        return forbidden('系统数据仅管理员可修改')
    return forbidden()


def owned(model, pk, owner_field='user_id', not_found_msg='记录不存在'):
    """按主键取资源并校验归属，返回 (obj, error)。"""
    obj = model.query.get(pk)
    if obj is None:
        return None, (jsonify({'code': 404, 'msg': not_found_msg}), 404)
    err = ensure_owner(obj, owner_field)
    if err:
        return None, err
    return obj, None


def register_jwt_error_handlers(jwt):
    """把 flask-jwt-extended 的默认错误改成前端约定的 {code, msg}。"""
    @jwt.unauthorized_loader
    def _missing(reason):
        return jsonify({'code': 401, 'msg': '请先登录'}), 401

    @jwt.invalid_token_loader
    def _invalid(reason):
        return jsonify({'code': 401, 'msg': '登录凭证无效，请重新登录'}), 401

    @jwt.expired_token_loader
    def _expired(header, payload):
        return jsonify({'code': 401, 'msg': '登录已过期，请重新登录'}), 401

    @jwt.revoked_token_loader
    def _revoked(header, payload):
        return jsonify({'code': 401, 'msg': '登录凭证已失效，请重新登录'}), 401
