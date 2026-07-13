import requests
import re
import json
from typing import List

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def _make_request(url: str, headers_extra: dict = None, timeout: int = 10) -> requests.Response:
    """通用请求封装"""
    h = {**HEADERS, **(headers_extra or {})}
    resp = requests.get(url, timeout=timeout, headers=h)
    resp.raise_for_status()
    return resp


def fetch_weibo_hot(limit: int = 5) -> dict:
    """微博热搜榜"""
    try:
        url = "https://weibo.com/ajax/side/hotSearch"
        resp = _make_request(url, {"Referer": "https://weibo.com/"})
        data = resp.json()
        items = []
        for item in data.get("data", {}).get("realtime", [])[:limit]:
            word = item.get("word", "")
            word = re.sub(r"#", "", word).strip()
            if word:
                items.append({
                    "title": word,
                    "url": f"https://s.weibo.com/weibo?q={word}"
                })
        return {"success": True, "source": "微博热搜", "items": items}
    except Exception as e:
        return {"success": False, "source": "微博热搜", "error": str(e), "items": []}


def fetch_baidu_hot(limit: int = 5) -> dict:
    """百度热搜榜"""
    try:
        url = "https://top.baidu.com/board?tab=realtime"
        resp = _make_request(url, {"Referer": "https://top.baidu.com/"})
        text = resp.text
        match = re.search(r'<!--s-data:(.*?)-->', text, re.DOTALL)
        if not match:
            return {"success": False, "source": "百度热搜", "error": "数据解析失败", "items": []}
        data = json.loads(match.group(1))
        cards = data.get("data", {}).get("cards", [{}])[0].get("content", [])
        items = []
        for card in cards[:limit]:
            title = card.get("word", "") or card.get("query", "")
            item_url = card.get("url", "") or f"https://www.baidu.com/s?wd={title}"
            if title:
                items.append({"title": title, "url": item_url})
        return {"success": True, "source": "百度热搜", "items": items}
    except Exception as e:
        return {"success": False, "source": "百度热搜", "error": str(e), "items": []}


def fetch_zhihu_hot(limit: int = 5) -> dict:
    """知乎热榜（搜索热榜 API）"""
    try:
        # 使用知乎搜索热榜 API，比页面抓取更稳定
        url = "https://www.zhihu.com/api/v4/search/top_search"
        resp = _make_request(url, {"Referer": "https://www.zhihu.com/"})
        data = resp.json()
        words = data.get("top_search", {}).get("words", [])
        items = []
        for w in words[:limit]:
            query = w.get("query", "")
            if query:
                items.append({
                    "title": query,
                    "url": f"https://www.zhihu.com/search?q={query}"
                })
        return {"success": True, "source": "知乎热榜", "items": items}
    except Exception as e:
        return {"success": False, "source": "知乎热榜", "error": str(e), "items": []}


def fetch_toutiao_hot(limit: int = 5) -> dict:
    """今日头条热榜"""
    try:
        url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
        resp = _make_request(url, {
            "Referer": "https://www.toutiao.com/",
            "Cookie": "tt_webid=0;"
        })
        text = resp.text

        items = []

        # 方式1: 尝试正则提取 ClusterId 和 Title
        clusters = re.findall(r'"ClusterId"\s*:\s*"(\d+)".*?"Title"\s*:\s*"([^"]*)"', text, re.DOTALL)
        if not clusters:
            clusters = re.findall(r'"ClusterId"\s*:\s*(\d+).*?"Title"\s*:\s*"([^"]*)"', text, re.DOTALL)

        if not clusters:
            # 方式2: 分开匹配 ClusterId 和 Title 的 JSON 块
            blocks = re.findall(r'\{(?:[^{}]|\{[^{}]*\})*"ClusterId"\s*:\s*"?(\d+)"?(?:[^{}]|\{[^{}]*\})*\}', text)
            titles = re.findall(r'"Title"\s*:\s*"([^"]*)"', text)

        for cid, title in clusters[:limit]:
            items.append({
                "title": title,
                "url": f"https://www.toutiao.com/trending/{cid}/" if cid else ""
            })

        if items:
            return {"success": True, "source": "头条热榜", "items": items}

        return {"success": False, "source": "头条热榜", "error": "数据解析失败", "items": []}
    except Exception as e:
        return {"success": False, "source": "头条热榜", "error": str(e), "items": []}


def fetch_all_hot_events(enabled: dict, limit: int = 5) -> List[dict]:
    """获取所有已启用的热点事件源"""
    results = []
    sources = {
        "weibo_hot": ("微博热搜", fetch_weibo_hot),
        "baidu_hot": ("百度热搜", fetch_baidu_hot),
        "zhihu_hot": ("知乎热榜", fetch_zhihu_hot),
        "toutiao_hot": ("头条热榜", fetch_toutiao_hot),
    }
    for key, (name, func) in sources.items():
        if enabled.get(key, True):
            r = func(limit=limit)
            r["name"] = name
            results.append(r)
    return results
