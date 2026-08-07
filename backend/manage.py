"""服务器管理脚本 — 解决僵尸进程问题"""
import os, sys, signal, time, subprocess, socket

PID_FILE = os.path.join(os.path.dirname(__file__), '.server.pid')
PORT = int(os.environ.get('PORT', 9876))
HOST = '0.0.0.0'


def find_free_port():
    """找空闲端口"""
    s = socket.socket()
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def is_port_free(port):
    """检查端口是否空闲"""
    s = socket.socket()
    try:
        s.bind((HOST, port))
        s.close()
        return True
    except OSError:
        return False


def _kill_tree(pid):
    """递归杀掉进程及其所有子进程（taskkill /T 一步到位，避免 wmic 卡死）"""
    try:
        pid = int(pid)
    except (ValueError, TypeError):
        return
    try:
        subprocess.run(['taskkill', '/T', '/F', '/PID', str(pid)],
                       capture_output=True, timeout=8, encoding='gbk')
    except Exception:
        pass


def _kill_port(port):
    """杀掉占用指定端口的进程（用 netstat 找 PID，再 taskkill 整棵树）"""
    if os.name != 'nt':
        return
    try:
        result = subprocess.run(
            f'netstat -ano | findstr ":{port}" | findstr LISTEN',
            shell=True, capture_output=True, text=True, timeout=8, encoding='gbk'
        )
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            parts = line.strip().split()
            if parts:
                _kill_tree(parts[-1])
    except Exception:
        pass


def kill_old():
    """杀旧进程"""
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            old_pid = f.read().strip()
        if old_pid:
            _kill_tree(old_pid)
            try:
                os.remove(PID_FILE)
            except OSError:
                pass
    # 额外清理：同端口旧进程
    _kill_port(PORT)


def start():
    """启动服务器"""
    kill_old()

    if not is_port_free(PORT):
        print(f'端口 {PORT} 仍被占用，尝试强制释放...')
        _kill_port(PORT)
        time.sleep(2)

    from app import create_app
    app = create_app()

    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

    print(f'服务器启动于 http://{HOST}:{PORT} (PID: {os.getpid()})')
    app.run(debug=False, port=PORT, host=HOST, use_reloader=False)


def stop():
    """停止服务器"""
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            pid = f.read().strip()
        if pid:
            _kill_tree(pid)
            print(f'已停止进程 {pid}')
        try:
            os.remove(PID_FILE)
        except OSError:
            pass
    else:
        print('没有运行中的服务器')


def restart():
    """重启服务器"""
    stop()
    time.sleep(1)
    start()


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'start'
    if cmd == 'start':
        start()
    elif cmd == 'stop':
        stop()
    elif cmd == 'restart':
        restart()
    elif cmd == 'port':
        print(find_free_port())
    else:
        print(f'用法: python manage.py [start|stop|restart]')
