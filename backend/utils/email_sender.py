"""邮件发送工具"""
import os
import smtplib
import socket
from email.mime.text import MIMEText
from email.header import Header


PLACEHOLDER_USERS = {'your_email@qq.com', ''}


def _smtp_configured(cfg):
    return (
        bool(cfg['user'])
        and cfg['user'] not in PLACEHOLDER_USERS
        and bool(cfg['password'])
    )


def get_smtp_config():
    return {
        'host': os.getenv('SMTP_HOST', ''),
        'port': int(os.getenv('SMTP_PORT', '587')),
        'user': os.getenv('SMTP_USER', ''),
        'password': os.getenv('SMTP_PASSWORD', ''),
        'sender': os.getenv('SMTP_SENDER', os.getenv('SMTP_USER', '')),
    }


def _try_send(cfg, to_email, msg, port, use_ssl):
    """尝试发送，返回 (ok, error)。"""
    try:
        if use_ssl:
            s = smtplib.SMTP_SSL(cfg['host'], port, timeout=10)
        else:
            s = smtplib.SMTP(cfg['host'], port, timeout=10)
            s.starttls()
        s.login(cfg['user'], cfg['password'])
        s.sendmail(cfg['sender'], [to_email], msg.as_string())
        s.quit()
        return True, None
    except (smtplib.SMTPException, OSError, socket.timeout) as e:
        return False, e


def send_verification_code(to_email, code):
    """发送验证码邮件 — 自动尝试 587(TLS) → 465(SSL) 回退"""
    cfg = get_smtp_config()
    if not _smtp_configured(cfg):
        print(f'[邮件] SMTP 未配置，请在 .env 中填写真实的 SMTP_USER 和 SMTP_PASSWORD')
        return False

    subject = '饮食管理系统 — 密码重置验证码'
    body = f'''
<div style="max-width:480px;margin:0 auto;padding:24px;font-family:sans-serif;border:1px solid #eee;border-radius:8px">
    <div style="text-align:center;margin-bottom:20px">
        <div style="width:48px;height:48px;background:#111;color:#fff;border-radius:8px;
                    display:inline-flex;align-items:center;justify-content:center;font-size:22px;font-weight:700">食</div>
        <h2 style="color:#111;margin:8px 0 0">密码重置</h2>
    </div>
    <p style="color:#555;font-size:14px;line-height:1.6">您正在重置饮食管理系统的登录密码，验证码如下：</p>
    <div style="text-align:center;margin:24px 0;font-size:36px;font-weight:700;letter-spacing:8px;color:#111">{code}</div>
    <p style="color:#999;font-size:12px">验证码有效期为10分钟，如非本人操作请忽略此邮件。</p>
</div>
'''

    msg = MIMEText(body, 'html', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = cfg['sender']
    msg['To'] = to_email

    attempts = []

    configured_port = cfg['port']
    if configured_port == 465:
        attempts.append((configured_port, True))
    elif configured_port == 587:
        attempts.append((configured_port, False))
    else:
        attempts.append((configured_port, configured_port == 465))

    fallback = 465 if configured_port != 465 else 587
    attempts.append((fallback, fallback == 465))

    last_error = None
    for port, use_ssl in attempts:
        ok, err = _try_send(cfg, to_email, msg, port, use_ssl)
        if ok:
            print(f'[邮件] 验证码已发送至 {to_email} (端口 {port})')
            return True
        last_error = err
        print(f'[邮件] 端口 {port} 失败: {err}')

    print(f'[邮件] 所有端口尝试均失败，最后错误: {last_error}')
    if isinstance(last_error, smtplib.SMTPAuthenticationError):
        print(f'[邮件] ⚠ 账号或密码错误！QQ邮箱请使用"授权码"而非登录密码')
        print(f'[邮件]    获取方式: QQ邮箱 → 设置 → 账户 → 生成授权码')
    elif isinstance(last_error, (ConnectionRefusedError, ConnectionResetError, OSError)):
        print(f'[邮件] ⚠ 无法连接到 {cfg["host"]}，请检查地址和端口是否正确')
        print(f'[邮件]    QQ邮箱: smtp.qq.com:587(SSL关) 或 smtp.qq.com:465(SSL开)')
        print(f'[邮件]    163邮箱: smtp.163.com:465(SSL开)')
    return False
