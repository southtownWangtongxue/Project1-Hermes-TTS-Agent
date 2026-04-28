"""Database configuration settings"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置设置"""

    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "password"
    DB_NAME: str = "hermes_tts_agent"

    # FastAPI 配置
    FASTAPI_HOST: str = "0.0.0.0"
    FASTAPI_PORT: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()
