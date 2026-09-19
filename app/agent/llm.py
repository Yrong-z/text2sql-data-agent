"""Lazy DeepSeek client used by SQL generation/correction nodes."""
from __future__ import annotations

from langchain_deepseek import ChatDeepSeek
from app.conf.app_config import app_config

_llm = None


def get_llm_client():
    global _llm
    if _llm is not None:
        return _llm
    api_key = (app_config.llm.api_key or "").strip()
    if not api_key:
        raise RuntimeError("LLM provider is not configured.")
    _llm = ChatDeepSeek(
        model=app_config.llm.model_name,
        timeout=30,
        max_retries=1,
        api_key=api_key,
        base_url=app_config.llm.base_url,
        temperature=0,
    )
    return _llm

if __name__ == "__main__":
    print(get_llm_client().invoke("你好").content)
