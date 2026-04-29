"""
依赖注入模块 —— 提供可复用的 FastAPI 依赖函数
"""
from app.core.config import Settings, settings


def get_settings() -> Settings:
    """
    获取应用配置实例。
    使用 FastAPI Depends 注入，方便测试时替换。
    """
    return settings
