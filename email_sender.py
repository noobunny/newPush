import os
import smtplib
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    to_emails: list,
    subject: str,
    html_body: str,
):
    """通过 SMTP 发送 HTML 邮件，支持多收件人"""
    print(f"   📧 SMTP 服务器: {smtp_host}:{smtp_port}")
    print(f"   📧 发件人: {smtp_user}")
    print(f"   📧 收件人: {to_emails}")
    print(f"   📧 密码长度: {len(smtp_password)} 字符（{smtp_password[:3]}***）")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = ", ".join(to_emails)

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        print(f"   🔗 正在连接 SMTP 服务器...")
        server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
        print(f"   🔗 连接成功，正在登录...")
        server.login(smtp_user, smtp_password)
        print(f"   🔐 登录成功，正在发送...")
        server.sendmail(smtp_user, to_emails, msg.as_string())
        server.quit()
        print(f"   ✅ 邮件发送成功！")
    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ SMTP 认证失败: {e}")
        print(f"   💡 提示: 163 邮箱需要使用「授权码」而非登录密码")
        print(f"   💡 请在 https://mail.163.com/ 设置 → POP3/SMTP/IMAP → 开启并获取授权码")
        raise
    except smtplib.SMTPConnectError as e:
        print(f"   ❌ SMTP 连接失败: {e}")
        print(f"   💡 提示: 检查 smtp_host 和 smtp_port 是否正确")
        raise
    except socket.timeout:
        print(f"   ❌ SMTP 连接超时（30秒）")
        print(f"   💡 提示: GitHub Actions 可能无法直接连接国内邮箱 SMTP")
        raise
    except Exception as e:
        print(f"   ❌ 发送邮件失败: {type(e).__name__}: {e}")
        print(f"   💡 完整错误: {repr(e)}")
        raise
