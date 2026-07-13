import os
import requests
from typing import Dict, Optional

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-v4-flash"

PROMPT_TEMPLATE = """你是一个专业的新闻编辑。请为以下每条新闻/热点标题写一段简短概述（80-150字），让读者看完就能了解事件全貌。

要求：
1. 严格按编号输出，每段格式为 "编号. 概述内容"
2. 概述要包含：发生了什么事、关键人物/机构、当前进展或影响
3. 用通俗易懂的中文，不要照搬标题措辞
4. 不要加任何额外前缀、解释或"本条新闻讲述了"之类的套话
5. 每条概述之间留一个空行

标题列表：
{titles}"""


def _call_deepseek(prompt: str, api_key: str, timeout: int = 60) -> Optional[str]:
    """调用 DeepSeek API"""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": "你是一个资深的新闻编辑，擅长用通俗易懂的语言概述新闻事件，让读者快速了解事件全貌。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.5,
            "max_tokens": 4096,
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
    """解析 AI 返回的编号概述"""
    summaries = {}
    # 按双换行（空行）或单换行分隔各条目
    # AI 可能在条目之间加了空行，先尝试按空行分
    blocks = response.split("\n\n")
    if len(blocks) < expected_count:
        # AI 没有加空行，按单换行分
        blocks = response.strip().split("\n")
        # 合并多行的同一条目
        merged = []
        current = ""
        for line in blocks:
            line = line.strip()
            if not line:
                continue
            # 检查是否以编号开头（如 "1. " 或 "1、"）
            is_new_item = False
            for sep in [". ", "、", ") ", "． "]:
                if sep in line[:8]:
                    try:
                        int(line.split(sep, 1)[0].strip())
                        is_new_item = True
                    except ValueError:
                        pass
                    break
            if is_new_item and current:
                merged.append(current)
                current = line
            elif is_new_item:
                current = line
            else:
                if current:
                    current += "\n" + line
                else:
                    current = line
        if current:
            merged.append(current)
        blocks = merged

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # 提取编号和内容
        for sep in [". ", "、", ") ", "． "]:
            if sep in block[:8]:
                parts = block.split(sep, 1)
                try:
                    num = int(parts[0].strip())
                    text = parts[1].strip()
                    if text and len(text) >= 5:
                        summaries[str(num)] = text
                except ValueError:
                    pass
                break
    return summaries


def batch_summarize(titles_by_id: Dict[str, str], api_key: str = None) -> Dict[str, str]:
    """
    批量生成 AI 概述

    Args:
        titles_by_id: {id: title} 字典
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

    print(f"   🤖 正在调用 AI 为 {len(items)} 条标题生成概述...")
    response = _call_deepseek(prompt, api_key)

    if not response:
        return {}

    summaries = _parse_summaries(response, len(items))

    # 将编号映射回原始 id
    result = {}
    for i, (item_id, title) in enumerate(items, 1):
        if str(i) in summaries:
            result[item_id] = summaries[str(i)]

    print(f"   ✅ AI 概述完成: {len(result)}/{len(items)} 条")
    return result
