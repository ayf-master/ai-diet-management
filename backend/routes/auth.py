import os
import time
from datetime import datetime
from flask import request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from app import db
from models import User, Admin, UserGoal, VerificationCode
from utils.auth import auth_required, ensure_self, issue_token
from utils.email_sender import send_verification_code
from . import api

ALLOWED_AVATAR_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}


@api.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'msg': '请求数据为空'}), 400

    account = data.get('account')
    password = data.get('password')
    if not account or not password:
        return jsonify({'code': 400, 'msg': '账号和密码不能为空'}), 400

    if User.query.filter_by(account=account).first():
        return jsonify({'code': 409, 'msg': '账号已存在'}), 409

    diet_goals = data.get('diet_goals', [data.get('diet_goal', 'healthy')])
    if not diet_goals:
        diet_goals = ['healthy']

    user = User(
        account=account,
        password=generate_password_hash(password),
        nickname=data.get('nickname', account),
        email=data.get('email'),
        age=data.get('age', 18),
        gender=data.get('gender', 0),
        height=data.get('height', 160),
        current_weight=data.get('current_weight', 60),
        target_weight=data.get('target_weight', 55),
        activity_level=data.get('activity_level', 1),
        diet_goal=diet_goals[0],
        recommend_cal=1500,
    )
    db.session.add(user)
    db.session.flush()

    for goal in diet_goals:
        ug = UserGoal(user_id=user.user_id, goal=goal)
        db.session.add(ug)

    db.session.commit()

    db.session.execute(
        db.text('CALL sp_recommend_daily_cal(:uid)'),
        {'uid': user.user_id}
    )
    db.session.commit()

    # 重新查询以加载所有关系
    user = User.query.get(user.user_id)

    return jsonify({
        'code': 200, 'msg': '注册成功',
        'data': user.to_dict(),
        'access_token': issue_token(user.user_id, role='user'),
    }), 200


@api.route('/user/profile', methods=['GET'])
@auth_required
def get_user_profile():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'code': 400, 'msg': '缺少user_id'}), 400
    err = ensure_self(user_id)
    if err:
        return err
    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'msg': '用户不存在'}), 404
    return jsonify({'code': 200, 'data': user.to_dict()})


@api.route('/user/zones', methods=['PUT'])
@auth_required
def update_user_zones():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    new_goals = data.get('diet_goals', [])
    if not user_id or not new_goals:
        return jsonify({'code': 400, 'msg': '参数错误'}), 400
    err = ensure_self(user_id)
    if err:
        return err

    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'msg': '用户不存在'}), 404

    if user.goals:
        latest = max(g.created_at for g in user.goals)
        # created_at 由 MySQL NOW()/db.func.now() 生成，使用服务器本地时间；
        # 故比较时也应使用本地时间，避免 UTC 与本地时区差导致负数天数。
        days_since = (datetime.now() - latest).days
        if days_since < 30:
            return jsonify({
                'code': 429,
                'msg': f'专区修改需间隔30天，还剩{30 - days_since}天',
                'data': {'days_remaining': 30 - days_since}
            }), 429

    UserGoal.query.filter_by(user_id=user_id).delete()
    for goal in new_goals:
        ug = UserGoal(user_id=user_id, goal=goal)
        db.session.add(ug)

    user.diet_goal = new_goals[0]
    db.session.commit()
    user = User.query.get(user.user_id)
    return jsonify({'code': 200, 'msg': '专区更新成功', 'data': user.to_dict()})


@api.route('/user/avatar', methods=['POST'])
@auth_required
def upload_avatar():
    user_id = request.form.get('user_id', type=int)
    if not user_id:
        return jsonify({'code': 400, 'msg': '缺少user_id'}), 400
    err = ensure_self(user_id)
    if err:
        return err

    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'msg': '用户不存在'}), 404

    file = request.files.get('avatar')
    if not file or file.filename == '':
        return jsonify({'code': 400, 'msg': '请选择头像文件'}), 400

    if file.content_type not in ALLOWED_AVATAR_TYPES:
        return jsonify({'code': 400, 'msg': '仅支持 JPG/PNG/WebP/GIF 图片'}), 400

    ext = secure_filename(file.filename).rsplit('.', 1)[-1].lower()
    if ext not in {'jpg', 'jpeg', 'png', 'webp', 'gif'}:
        ext = 'png'

    filename = f"{user_id}_{int(time.time())}.{ext}"
    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

    # 清理旧头像
    if user.avatar_url:
        old_name = user.avatar_url.rsplit('/', 1)[-1]
        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], old_name)
        try:
            if os.path.exists(old_path):
                os.remove(old_path)
        except Exception:
            pass

    file.save(save_path)

    avatar_url = f"{current_app.config['AVATAR_URL_PREFIX']}/{filename}"
    user.avatar_url = avatar_url
    db.session.commit()

    return jsonify({'code': 200, 'msg': '头像上传成功', 'data': {'avatar_url': avatar_url}})


@api.route('/user/avatar', methods=['DELETE'])
@auth_required
def remove_avatar():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'code': 400, 'msg': '缺少user_id'}), 400
    err = ensure_self(user_id)
    if err:
        return err

    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'msg': '用户不存在'}), 404

    # 删除磁盘上的旧头像文件
    if user.avatar_url:
        old_name = user.avatar_url.rsplit('/', 1)[-1]
        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], old_name)
        try:
            if os.path.exists(old_path):
                os.remove(old_path)
        except Exception:
            pass
        user.avatar_url = ''
        db.session.commit()

    return jsonify({'code': 200, 'msg': '头像已移除', 'data': {'avatar_url': ''}})


@api.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'msg': '请求数据为空'}), 400

    user = User.query.filter_by(account=data.get('account')).first()
    if not user or not check_password_hash(user.password, data.get('password', '')):
        return jsonify({'code': 401, 'msg': '账号或密码错误'}), 401

    return jsonify({
        'code': 200, 'msg': '登录成功',
        'data': user.to_dict(),
        'access_token': issue_token(user.user_id, role='user'),
    }), 200


@api.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'msg': '请求数据为空'}), 400

    admin = Admin.query.filter_by(account=data.get('account')).first()
    if not admin or not check_password_hash(admin.password, data.get('password', '')):
        return jsonify({'code': 401, 'msg': '账号或密码错误'}), 401

    return jsonify({
        'code': 200, 'msg': '登录成功',
        'data': admin.to_dict(),
        'access_token': issue_token(admin.admin_id, role='admin', admin_id=admin.admin_id),
    }), 200


@api.route('/send-code', methods=['POST'])
def send_code():
    """发送验证码到用户注册邮箱"""
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'msg': '请求数据为空'}), 400

    account = data.get('account', '').strip()
    if not account:
        return jsonify({'code': 400, 'msg': '请输入账号'}), 400

    user = User.query.filter_by(account=account).first()
    if not user:
        return jsonify({'code': 404, 'msg': '账号不存在'}), 404
    if not user.email:
        return jsonify({'code': 400, 'msg': '该账号未绑定邮箱，无法找回密码'}), 400

    import os
    code = VerificationCode.generate(user.email)
    ok = send_verification_code(user.email, code)

    # SMTP 未配置时，开发模式直接返回验证码（方便调试）
    if not ok:
        from utils.email_sender import _smtp_configured, get_smtp_config
        if not _smtp_configured(get_smtp_config()):
            return jsonify({
                'code': 200,
                'msg': f'验证码已发送至 {user.email}（开发模式）',
                'dev_code': code,
                'dev_mode': True,
            }), 200
        return jsonify({'code': 500, 'msg': '验证码发送失败，请检查服务器邮件配置'}), 500

    return jsonify({'code': 200, 'msg': f'验证码已发送至 {user.email[:3]}***@{user.email.split("@")[1]}'}), 200


@api.route('/reset-password', methods=['POST'])
def reset_password():
    """验证码校验 + 重置密码"""
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'msg': '请求数据为空'}), 400

    account = data.get('account', '').strip()
    code = data.get('code', '').strip()
    new_password = data.get('password', '')

    if not account or not code or not new_password:
        return jsonify({'code': 400, 'msg': '账号、验证码和新密码不能为空'}), 400
    if len(new_password) < 6:
        return jsonify({'code': 400, 'msg': '密码长度至少6位'}), 400

    user = User.query.filter_by(account=account).first()
    if not user:
        return jsonify({'code': 404, 'msg': '账号不存在'}), 404
    if not user.email:
        return jsonify({'code': 400, 'msg': '该账号未绑定邮箱'}), 400

    if not VerificationCode.verify(user.email, code):
        return jsonify({'code': 400, 'msg': '验证码无效或已过期'}), 400

    user.password = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({'code': 200, 'msg': '密码重置成功，请用新密码登录'}), 200
