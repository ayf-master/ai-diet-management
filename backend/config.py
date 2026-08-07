import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
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
