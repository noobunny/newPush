#!/usr/bin/env python3
"""
每日新闻速览 · 邮件推送
- 并行拉取天气、热点、新闻、微语、农历
- AI 智能摘要热点事件和新闻标题
- 渲染 HTML 邮件模板
- 通过 SMTP 发送
"""
import os
import sys
import random
import yaml
import time
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor, as_completed
from jinja2 import Environment, FileSystemLoader

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sources import weather, hot_events, news, quote, holiday, ai_summary, it_knowledge
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
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    wd = weekdays[today.weekday()]
    solar = today.strftime("%Y年%m月%d日")

    lunar_info = holiday.get_lunar_info(today)
    lunar_str = lunar_info.get("lunar_chinese", "") if lunar_info.get("success") else ""

    return {
        "solar": solar,
        "weekday": wd,
        "lunar": lunar_str,
    }


def enrich_with_ai(hot_list, news_categories, ai_enabled: bool) -> bool:
    """
    为热点事件和新闻标题添加 AI 摘要
    返回是否有任何 AI 摘要生成成功
    """
    if not ai_enabled:
        return False

    # 收集所有标题，按序号建立 {n1: title, n2: title, ...} 映射
    # 同时记录每个序号对应的 item 引用
    titles_by_id = {}
    num_to_item = {}  # {序号: item引用}
    seq = 0

    for source in hot_list:
        if source.get("success"):
            for item in source.get("items", []):
                seq += 1
                key = f"n{seq}"
                titles_by_id[key] = item["title"]
                num_to_item[seq] = item

    for cat in news_categories:
        if cat.get("success"):
            for item in cat.get("items", []):
                seq += 1
                key = f"n{seq}"
                titles_by_id[key] = item["title"]
                num_to_item[seq] = item

    if not titles_by_id:
        return False

    # 批量调用 AI（AI 内部会将序号 1,2,3... 映射回 titles_by_id 的 key）
    print(f"🤖 AI 摘要: 共 {len(titles_by_id)} 条标题")
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    summaries = ai_summary.batch_summarize(titles_by_id, api_key)

    if not summaries:
        return False

    # 回填摘要：通过序号找到对应的 item
    for seq_num, item in num_to_item.items():
        key = f"n{seq_num}"
        if key in summaries:
            item["summary"] = summaries[key]

    return True


def main():
    t_start = time.time()
    cfg = load_config()
    email_cfg = cfg["email"]
    sections = cfg.get("sections", {})
    limits = cfg.get("limits", {})
    ai_cfg = cfg.get("ai", {})

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

    # 1. 日期 & 农历（本地计算，不需要网络）
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

    # 2. 并行获取：天气 + 4 个热点源 + 4 个新闻分类 + 微语
    print("\n⏳ 并行获取天气、热点、新闻、微语...")
    executor = ThreadPoolExecutor(max_workers=10)
    future_to_key = {}  # future -> key 反向映射

    # 2a. 天气
    weather_data = None
    if cfg.get("weather", {}).get("enabled", True):
        f = executor.submit(weather.fetch_weather, cfg["weather"]["city"])
        future_to_key[f] = "weather"

    # 2b. 热点事件 4 个源
    hot_sources = {
        "weibo_hot": ("微博热搜", hot_events.fetch_weibo_hot),
        "baidu_hot": ("百度热搜", hot_events.fetch_baidu_hot),
        "zhihu_hot": ("知乎热榜", hot_events.fetch_zhihu_hot),
        "toutiao_hot": ("头条热榜", hot_events.fetch_toutiao_hot),
    }
    hot_limit = limits.get("hot_events", 5)
    for key, (name, func) in hot_sources.items():
        if sections.get(key, True):
            f = executor.submit(func, hot_limit)
            future_to_key[f] = f"hot:{key}:{name}"

    # 2c. 新闻 4 个分类
    news_cat_map = {
        "domestic_news": "domestic",
        "economy_news": "economy",
        "tech_news": "tech",
        "world_news": "world",
    }
    news_limit = limits.get("news_per_category", 3)
    for section_key, cat_key in news_cat_map.items():
        if sections.get(section_key, True):
            f = executor.submit(news.fetch_category_news, cat_key, news_limit)
            future_to_key[f] = f"news:{cat_key}"

    # 2d. 每日微语
    if sections.get("daily_quote", True):
        f = executor.submit(quote.fetch_quote)
        future_to_key[f] = "quote"

    # 2e. 每日IT知识点（和 AI 摘要共用一个 key，异步并行）
    it_knowledge_data = None
    if sections.get("it_knowledge", True):
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        f = executor.submit(it_knowledge.fetch_knowledge, api_key)
        future_to_key[f] = "it_knowledge"

    # 等待所有结果
    hot_list = []
    news_results = []
    daily_quote = None
    it_knowledge_data = None
    hot_source_names = {k: v[0] for k, v in hot_sources.items()}

    for future in as_completed(future_to_key):
        key = future_to_key[future]
        try:
            result = future.result(timeout=15)
        except Exception as e:
            print(f"   ❌ {key} 异常: {e}")
            if key == "weather":
                weather_data = {"success": False, "error": str(e), "city": cfg["weather"]["city"]}
            elif key.startswith("hot:"):
                _, source_key, name = key.split(":", 2)
                hot_list.append({
                    "success": False, "name": name, "source": name,
                    "error": str(e), "items": [],
                })
            elif key.startswith("news:"):
                cat_key = key.split(":", 1)[1]
                news_results.append({
                    "category": cat_key, "items": [], "success": False,
                })
            elif key == "quote":
                fb = random.choice(quote.FALLBACK_QUOTES)
                daily_quote = {"success": True, "text": fb["text"], "source": fb["source"]}
            elif key == "it_knowledge":
                item = random.choice(it_knowledge.FALLBACK_KNOWLEDGE)
                it_knowledge_data = {"success": True, "title": item["title"], "description": item["description"]}
            continue

        if key == "weather":
            weather_data = result
            if result.get("success"):
                print(f"   ☀️  天气: {result['weather_desc']} {result['temp_min']}-{result['temp_max']}°C")
            else:
                print(f"   ⚠️  天气获取失败: {result.get('error', '')}")
        elif key.startswith("hot:"):
            _, source_key, name = key.split(":", 2)
            result["name"] = name
            hot_list.append(result)
            status = "✅" if result.get("success") else "❌"
            count = len(result.get("items", []))
            print(f"   {status} {name}: {count} 条")
        elif key.startswith("news:"):
            cat_key = key.split(":", 1)[1]
            news_results.append(result)
            status = "✅" if result.get("success") else "❌"
            count = len(result.get("items", []))
            print(f"   {status} {cat_key}: {count} 条")
        elif key == "quote":
            daily_quote = result
            if result.get("success"):
                print(f"   💬 微语: {result['text'][:30]}...")
            else:
                print(f"   ⚠️  微语获取失败")
        elif key == "it_knowledge":
            it_knowledge_data = result
            if result.get("success"):
                print(f"   💡 IT知识点: {result['title'][:30]}...")
            else:
                print(f"   ⚠️  IT知识点获取失败")

    executor.shutdown(wait=False)
    t_network = time.time() - t_start
    print(f"   ⏱️  网络请求耗时: {t_network:.1f}s")

    # 3. AI 智能摘要（热点 + 新闻）
    has_ai = enrich_with_ai(hot_list, news_results, ai_cfg.get("enabled", True))
    t_ai = time.time() - t_start
    if has_ai:
        print(f"   ⏱️  AI 摘要耗时: {t_ai - t_network:.1f}s")

    # 4. 渲染 HTML
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
        news_categories=news_results,
        quote=daily_quote,
        it_knowledge=it_knowledge_data,
        has_ai_summary=has_ai,
        generated_at=now.strftime("%Y-%m-%d %H:%M"),
    )

    # 5. 发送邮件
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

    t_total = time.time() - t_start
    print("=" * 50)
    print(f"✅ 邮件发送成功！总耗时 {t_total:.1f}s")
    print("=" * 50)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\n" + "=" * 50)
        print(f"💥 脚本执行失败: {type(e).__name__}: {e}")
        print(f"💥 完整错误: {repr(e)}")
        import traceback
        traceback.print_exc()
        print("=" * 50)
        sys.exit(1)
