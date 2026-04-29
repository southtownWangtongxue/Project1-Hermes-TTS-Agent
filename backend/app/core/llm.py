"""
LLM 客户端模块 —— 提供 OpenAI 兼容的 LLM 调用接口
使用 openai SDK 兼容 Qwen/GLM 等模型（通过自定义 base_url）
"""
from openai import AsyncOpenAI

from app.core.config import settings


def get_llm() -> AsyncOpenAI:
    """
    获取配置好的 AsyncOpenAI 客户端实例。

    自动从全局配置中读取 API Key、Base URL 等参数，
    每次调用创建新实例以保证线程安全。
    """
    return AsyncOpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
    )
