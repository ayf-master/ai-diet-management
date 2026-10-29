import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    # 会话与 JWT（生产环境必须在 .env 里覆盖 SECRET_KEY）
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-in-production-32bytes!')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)

    # 数据库
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'diet_management')

    SQLALCHEMY_DATABASE_URI = (
        f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}'
        f'@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        f'?charset=utf8mb4'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 上传
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'avatars')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
    AVATAR_URL_PREFIX = '/static/avatars'

    # AI
    AI_API_KEY = os.getenv('AI_API_KEY', '')
    AI_API_URL = os.getenv('AI_API_URL', '')
    AI_MODEL = os.getenv('AI_MODEL', 'gpt-4o')
