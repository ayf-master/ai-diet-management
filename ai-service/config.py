# AI 独立服务配置：从 backend/.env 读取共享密钥，本服务不单独存密钥
import os

from dotenv import load_dotenv

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 优先读 ai-service/.env（可覆盖），再读 backend/.env（DB 与 AI 密钥共享源）
load_dotenv(os.path.join(_BASE_DIR, '.env'))
load_dotenv(os.path.join(_BASE_DIR, '..', 'backend', '.env'))

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

# AI
AI_API_KEY = os.getenv('AI_API_KEY', '')
AI_API_URL = os.getenv('AI_API_URL', '')
AI_MODEL = os.getenv('AI_MODEL', 'deepseek-chat')

# 服务间内部鉴权（Spring 调用时必须带相同 token）
INTERNAL_TOKEN = os.getenv('INTERNAL_TOKEN', 'internal-dev-token-change-me')

PORT = int(os.getenv('AI_SERVICE_PORT', '9877'))
HOST = os.getenv('AI_SERVICE_HOST', '127.0.0.1')
