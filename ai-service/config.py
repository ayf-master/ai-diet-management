# AI 独立服务配置：容器内走环境变量，本地开发兼容 .env 文件
import os

from dotenv import load_dotenv

# 本地开发仍可放 .env；容器里该文件不存在，完全依赖环境变量注入
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_env_file = os.path.join(_BASE_DIR, '.env')
if os.path.exists(_env_file):
    load_dotenv(_env_file)

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
# 容器内必须监听 0.0.0.0，否则 Spring 容器无法通过服务名访问
HOST = os.getenv('AI_SERVICE_HOST', '0.0.0.0')
