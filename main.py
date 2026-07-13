#!/usr/bin/env python3
"""
每日新闻速览 · 邮件推送
- 并行拉取天气、热点、新闻、微语、农历
- 渲染 HTML 邮件模板
- 通过 SMTP 发送
"""
import os
import sys
import yaml
from datetime import datetime, date
from jinja2 import Environment, FileSystemLoader

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sources import weather, hot_events, news, quote, holiday
from email_sender import send_email


def load_config():
    """加载配置，敏感项优先从环境变量读取"""
    cfg_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # 环境变量覆盖（适用于 GitHub Actions）
    cfg["email"]["smtp_user"] = os.environ.get("SMTP_USER") or cfg["email"].get("smtp_user", "")
    cfg["email"]["smtp_password"] = os.environ.get("SMTP_PASSWORD") or cfg["email"].get("smtp_password", "")
    to_raw = os.environ.get("TO_EMAIL") or cfg["email"].get("to_email", "")
    # 支持逗号分隔多邮箱
    cfg["email"]["to_emails"] = [e.strip() for e in to_raw.split(",") if e.strip()]

    return cfg


def build_date_info() -> dict:
    """构建日期信息"""
    today = date.today()
    weekdays = ["星期一", "星期二", "星期三", "四", "五", "六", "日"]
    wd = weekdays[today.weekday()]
    solar = today.strftime("%Y年%m月%d日")

    lunar_info = holiday.get_lunar_info(today)
    lunar_str = lunar_info.get("lunar_chinese", "") if lunar_info.get("success") else ""

    return {
        "solar": solar,
        "weekday": wd,
        "lunar": lunar_str,
    }


def main():
    cfg = load_config()
    email_cfg = cfg["email"]
    sections = cfg.get("sections", {})
    limits = cfg.get("limits", {})

    # 验证必要配置
    if not email_cfg.get("smtp_user"):
        print("❌ 错误: 未配置 SMTP_USER")
        sys.exit(1)
    if not email_cfg.get("smtp_password"):
        print("❌ 错误: 未配置 SMTP_PASSWORD")
        sys.exit(1)
    if not email_cfg.get("to_emails"):
        print("❌ 错误: 未配置 TO_EMAIL")
        sys.exit(1)

    print("=" * 50)
    print("📋 每日新闻速览 · 开始生成")
    print("=" * 50)

    # 1. 日期 & 农历 & 倒计时
    print("📅 获取日期信息...")
    date_info = build_date_info()
    next_holiday = None
    if sections.get("holiday_countdown", True):
        print("🎯 计算节日倒计时...")
        next_holiday = holiday.get_next_holiday()
        if next_holiday:
            print(f"   距离「{next_holiday['name']}」还有 {next_holiday['days_away']} 天")
        else:
            print("   未找到下一个节日")

    # 2. 天气
    weather_data = None
    if cfg.get("weather", {}).get("enabled", True):
        print(f"☀️  获取天气 ({cfg['weather']['city']})...")
        weather_data = weather.fetch_weather(cfg["weather"]["city"])
        if weather_data.get("success"):
            print(f"   {weather_data['weather_desc']} {weather_data['temp_min']}-{weather_data['temp_max']}°C")
        else:
            print(f"   天气获取失败: {weather_data.get('error')}")

    # 3. 热点事件
    hot_list = []
    print("🔥 获取热点事件...")
    hot_limit = limits.get("hot_events", 5)
    hot_list = hot_events.fetch_all_hot_events(sections, limit=hot_limit)
    for h in hot_list:
        status = "✅" if h.get("success") else "❌"
        count = len(h.get("items", []))
        print(f"   {status} {h['name']}: {count} 条")

    # 4. 分类新闻
    print("📰 获取分类新闻...")
    news_limit = limits.get("news_per_category", 3)
    news_categories = news.fetch_all_news(sections, limit=news_limit)
    for cat in news_categories:
        status = "✅" if cat.get("success") else "❌"
        count = len(cat.get("items", []))
        print(f"   {status} {cat['category']}: {count} 条")

    # 5. 每日微语
    daily_quote = None
    if sections.get("daily_quote", True):
        print("💬 获取每日微语...")
        daily_quote = quote.fetch_quote()
        if daily_quote.get("success"):
            print(f"   {daily_quote['text'][:30]}...")
        else:
            print(f"   使用备用微语")

    # 6. 渲染 HTML
    print("✍️  渲染邮件模板...")
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("daily.html")

    now = datetime.now()
    subject = f"📋 每日新闻速览 · {now.strftime('%m/%d')}"

    html_body = template.render(
        date_info=date_info,
        holiday=next_holiday,
        weather=weather_data,
        hot_events=hot_list,
        news_categories=news_categories,
        quote=daily_quote,
        generated_at=now.strftime("%Y-%m-%d %H:%M"),
    )

    # 7. 发送邮件
    print(f"📧 发送邮件到 {', '.join(email_cfg['to_emails'])}...")
    send_email(
        smtp_host=email_cfg["smtp_host"],
        smtp_port=email_cfg["smtp_port"],
        smtp_user=email_cfg["smtp_user"],
        smtp_password=email_cfg["smtp_password"],
        to_emails=email_cfg["to_emails"],
        subject=subject,
        html_body=html_body,
    )

    print("=" * 50)
    print("✅ 邮件发送成功！")
    print("=" * 50)


if __name__ == "__main__":
    main()
