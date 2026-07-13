import os
import json
import requests
from typing import Dict, List, Optional

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-v4-flash"

PROMPT_TEMPLATE = """你是一个专业的新闻摘要助手。请为以下每条新闻/热点标题生成一句简短的中文摘要（不超过35字），让读者一眼了解事件核心。

要求：
1. 严格按编号输出，每行一条，格式为 "编号. 摘要内容"
2. 摘要要包含关键信息（谁、什么事、结果/影响）
3. 不要重复标题原文，要用自己的话概括
4. 不要加任何额外解释或前缀

标题列表：
{titles}"""


def _call_deepseek(prompt: str, api_key: str, timeout: int = 45) -> Optional[str]:
    """调用 DeepSeek API"""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": "你是一个专业的新闻摘要助手，擅长用一句话概括新闻事件的核心。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 2048,
            "thinking": {"type": "disabled"},
        }
        resp = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return content.strip() if content else None
    except Exception as e:
        print(f"   ⚠️  AI 摘要请求失败: {e}")
        return None


def _parse_summaries(response: str, expected_count: int) -> Dict[str, str]:
    """解析 AI 返回的编号摘要"""
    summaries = {}
    lines = response.strip().split("\n")
    for line in lines:
        line = line.strip()
        # 匹配 "1. xxx" 或 "1、xxx" 或 "1) xxx" 格式
        if not line:
            continue
        # 尝试提取编号和内容
        for sep in [". ", "、", ") ", "． "]:
            if sep in line:
                parts = line.split(sep, 1)
                try:
                    num = int(parts[0].strip())
                    text = parts[1].strip()
                    if text:
                        summaries[str(num)] = text
                except ValueError:
                    pass
                break
    return summaries


def batch_summarize(titles_by_id: Dict[str, str], api_key: str = None) -> Dict[str, str]:
    """
    批量生成 AI 摘要

    Args:
        titles_by_id: {id: title} 字典，id 用于匹配返回结果
        api_key: DeepSeek API key

    Returns:
        {id: summary_text} 字典
    """
    if not api_key:
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")

    if not api_key or not titles_by_id:
        return {}

    # 构建编号列表
    items = list(titles_by_id.items())
    numbered_lines = []
    for i, (item_id, title) in enumerate(items, 1):
        numbered_lines.append(f"{i}. {title}")

    prompt = PROMPT_TEMPLATE.format(titles="\n".join(numbered_lines))

    print(f"   🤖 正在调用 AI 为 {len(items)} 条标题生成摘要...")
    response = _call_deepseek(prompt, api_key)

    if not response:
        return {}

    summaries = _parse_summaries(response, len(items))

    # 将编号映射回原始 id
    result = {}
    for i, (item_id, title) in enumerate(items, 1):
        if str(i) in summaries:
            result[item_id] = summaries[str(i)]

    print(f"   ✅ AI 摘要完成: {len(result)}/{len(items)} 条")
    return result
