import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from services.errors import DomainError

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    CORS(app)
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    from utils.auth import register_jwt_error_handlers
    register_jwt_error_handlers(jwt)

    from routes import api
    app.register_blueprint(api)

    @app.errorhandler(DomainError)
    def handle_domain_error(err):
        return jsonify({'code': err.code, 'msg': err.message}), err.code

    with app.app_context():
        # 只是导入模型，让 SQLAlchemy/Alembic 完成注册；建表与升级统一走 flask db upgrade
        from models import User, Admin, VerificationCode, Recipe, CookingMethod, UserCookingPref  # noqa: F401

    return app
