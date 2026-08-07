import os
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    CORS(app)
    db.init_app(app)

    from routes import api
    app.register_blueprint(api)

    with app.app_context():
        from models import User, Admin, VerificationCode, Recipe, CookingMethod, UserCookingPref  # 注册模型
        db.create_all()

    return app
