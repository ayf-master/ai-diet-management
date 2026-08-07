"""启动服务器 — 委托给 manage.py"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from manage import start

start()
