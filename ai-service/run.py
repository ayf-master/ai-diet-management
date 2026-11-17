# 启动 AI 独立服务
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app  # noqa: E402
from config import HOST, PORT  # noqa: E402

if __name__ == '__main__':
    print(f'AI 服务启动于 http://{HOST}:{PORT}')
    app.run(debug=False, port=PORT, host=HOST, use_reloader=False)
