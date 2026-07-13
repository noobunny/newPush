import requests


def fetch_quote() -> dict:
    """从 Hitokoto 一言 API 获取每日微语"""
    try:
        resp = requests.get(
            "https://v1.hitokoto.cn/",
            params={"c": "a"},
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "success": True,
            "text": data.get("hitokoto", ""),
            "source": data.get("from", ""),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "text": "把平凡的日子过得认真，把简单的事情做到极致，时间会给你最好的答案。",
            "source": "备用微语",
        }
