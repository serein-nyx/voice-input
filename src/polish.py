"""调用 DeepSeek（OpenAI 兼容接口）用 prompt-v4 润色转写文本。"""
import re

import requests

from . import config

_SYSTEM_PROMPT: str | None = None


def _load_prompt() -> str:
    global _SYSTEM_PROMPT
    if _SYSTEM_PROMPT is None:
        _SYSTEM_PROMPT = config.PROMPT_FILE.read_text(encoding="utf-8").strip()
    return _SYSTEM_PROMPT


def _strip_wrapping(text: str) -> str:
    """防御性去壳：模型偶尔会包一层 ```...``` 代码块。"""
    text = text.strip()
    fence = re.match(r"^```[a-zA-Z]*\n(.*)\n```$", text, re.DOTALL)
    if fence:
        return fence.group(1).strip()
    return text


def polish(transcript: str) -> str:
    """把转写文本润色为最终文本。失败时抛出异常，由调用方决定降级策略。"""
    if not transcript.strip():
        return ""
    if not config.DEEPSEEK_API_KEY:
        raise RuntimeError("缺少 DEEPSEEK_API_KEY，请在 .env 中配置")

    url = f"{config.DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions"
    payload = {
        "model": config.DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": _load_prompt()},
            {"role": "user", "content": transcript},
        ],
        "temperature": config.LLM_TEMPERATURE,
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {config.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=config.LLM_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    return _strip_wrapping(content)
