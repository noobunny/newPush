import requests
import json
import feedparser
from typing import List

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
}

FEEDS = {
    "domestic": [
        ("人民网", "http://www.people.com.cn/rss/politics.xml"),
        ("新华网", "http://www.xinhuanet.com/politics/xhll.xml"),
    ],
    "economy": [
        ("新浪财经", "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&num=10"),
        ("东方财富", "https://np-listapi.eastmoney.com/comm/webapp/relate/getBusinessNews?limit=10"),
    ],
    "tech": [
        ("36氪", "https://36kr.com/feed"),
        ("虎嗅网", "https://www.huxiu.com/rss/0.xml"),
        ("少数派", "https://sspai.com/feed"),
    ],
    "world": [
        ("Google News", "https://news.google.com/rss/search?q=china+world&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"),
    ],
}


def _fetch_feed(url: str, timeout: int = 10) -> list:
    """抓取 RSS/Atom 源"""
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:5]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "")
            if title:
                items.append({"title": title, "url": link})
        return items
    except Exception:
        return []


def _fetch_sina_finance_api(url: str, timeout: int = 10) -> list:
    """新浪财经 JSON API"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        data = resp.json()
        items = []
        for item in data.get("result", {}).get("data", [])[:5]:
            title = item.get("title", "").strip()
            link = item.get("url", "")
            if title:
                items.append({"title": title, "url": link})
        return items
    except Exception:
        return []


def _fetch_eastmoney_api(url: str, timeout: int = 10) -> list:
    """东方财富 JSON API"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        data = resp.json()
        items = []
        for item in (data.get("data", []) if isinstance(data, dict) else [])[:5]:
            title = item.get("title", "").strip()
            link = item.get("url", "") or item.get("share_link", "")
            if title:
                items.append({"title": title, "url": link})
        return items
    except Exception:
        return []


def _fetch_rsshub(url: str, timeout: int = 10) -> list:
    """RSSHub API"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        feed = feedparser.parse(resp.text)
        items = []
        for entry in feed.entries[:5]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "")
            if title:
                items.append({"title": title, "url": link})
        return items
    except Exception:
        return []


# 特殊源处理器
SPECIAL_FETCHERS = {
    "新浪财经": _fetch_sina_finance_api,
    "东方财富": _fetch_eastmoney_api,
}


def fetch_category_news(category: str, limit: int = 3) -> dict:
    """抓取某个分类的新闻，从多个源聚合"""
    sources = FEEDS.get(category, [])
    all_items = []
    for name, url in sources:
        # 选择获取方式
        if name in SPECIAL_FETCHERS:
            items = SPECIAL_FETCHERS[name](url)
        elif "rsshub.app" in url:
            items = _fetch_rsshub(url)
        else:
            items = _fetch_feed(url)
        for item in items:
            all_items.append(item)

    # 去重（按标题）
    seen = set()
    unique = []
    for item in all_items:
        if item["title"] not in seen:
            seen.add(item["title"])
            unique.append(item)
            if len(unique) >= limit:
                break

    return {
        "category": category,
        "items": unique[:limit],
        "success": len(unique) > 0,
    }


def fetch_all_news(enabled: dict, limit: int = 3) -> List[dict]:
    """获取所有已启用的新闻分类"""
    results = []
    categories = {
        "domestic_news": "domestic",
        "economy_news": "economy",
        "tech_news": "tech",
        "world_news": "world",
    }
    for section_key, cat_key in categories.items():
        if enabled.get(section_key, True):
            results.append(fetch_category_news(cat_key, limit=limit))
    return results
