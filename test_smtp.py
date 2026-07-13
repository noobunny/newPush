#!/usr/bin/env python3
"""SMTP 连接测试脚本 — 验证邮箱凭据是否可用"""
import os
import sys
import smtplib
import socket

print("=" * 50)
print("📧 SMTP 连接测试")
print("=" * 50)

# 从环境变量或 config.yaml 读取
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.163.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

if not SMTP_USER or not SMTP_PASSWORD:
    print("❌ 请先设置环境变量:")
    print("   export SMTP_USER='your@163.com'")
    print("   export SMTP_PASSWORD='你的授权码'")
    print()
    print("💡 163 邮箱授权码获取步骤:")
    print("   1. 登录 https://mail.163.com/")
    print("   2. 设置 → POP3/SMTP/IMAP")
    print("   3. 开启「IMAP/SMTP服务」或「POP3/SMTP服务」")
    print("   4. 按提示发送短信获取「授权码」")
    print("   5. 将授权码填入 SMTP_PASSWORD（不是邮箱登录密码！）")
    sys.exit(1)

print(f"SMTP 服务器: {SMTP_HOST}:{SMTP_PORT}")
print(f"发件人: {SMTP_USER}")
print()

# Test 1: DNS resolution
print("1️⃣  测试 DNS 解析...")
try:
    ip = socket.getaddrinfo(SMTP_HOST, SMTP_PORT)
    print(f"   ✅ DNS 解析成功: {ip[0][4]}")
except Exception as e:
    print(f"   ❌ DNS 解析失败: {e}")
    print("   💡 GitHub Actions 可能无法解析国内邮箱域名")
    sys.exit(1)

# Test 2: TCP connection
print("2️⃣  测试 TCP 连接...")
try:
    sock = socket.create_connection((SMTP_HOST, SMTP_PORT), timeout=15)
    sock.close()
    print(f"   ✅ TCP 连接成功")
except Exception as e:
    print(f"   ❌ TCP 连接失败: {e}")
    print("   💡 GitHub Actions 可能无法直连国内 SMTP 服务器")
    sys.exit(1)

# Test 3: SMTP SSL handshake
print("3️⃣  测试 SMTP SSL 握手...")
try:
    server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15)
    print(f"   ✅ SSL 握手成功")
except Exception as e:
    print(f"   ❌ SSL 握手失败: {e}")
    sys.exit(1)

# Test 4: Login
print("4️⃣  测试登录...")
try:
    server.login(SMTP_USER, SMTP_PASSWORD)
    print(f"   ✅ 登录成功！凭据有效")
except smtplib.SMTPAuthenticationError as e:
    print(f"   ❌ 认证失败: {e}")
    print()
    print("   💡 常见原因:")
    print("      a) SMTP_PASSWORD 填的是邮箱登录密码 → 需要用「授权码」")
    print("      b) 授权码过期或输入错误（注意大小写和空格）")
    print("      c) 没有在 163 邮箱设置中开启 SMTP 服务")
    server.quit()
    sys.exit(1)
except Exception as e:
    print(f"   ❌ 登录异常: {e}")
    server.quit()
    sys.exit(1)

server.quit()
print()
print("=" * 50)
print("✅ 所有测试通过！SMTP 凭据正常，可以发送邮件")
print("=" * 50)
