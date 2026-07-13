import os
import smtplib
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
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = ", ".join(to_emails)

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_emails, msg.as_string())
