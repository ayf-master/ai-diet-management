"""WSGI 入口：给 flask CLI（flask db ...）和 gunicorn 使用。"""
from app import create_app

app = create_app()
