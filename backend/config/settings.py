from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator
from pathlib import Path
import os
import sys

class Settings(BaseSettings):
    # Database
    DB_HOST: str = "mysql"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "root"
    DB_NAME: str = "hermes"

    # FastAPI
    FASTAPI_HOST: str = "0.0.0.0"
    FASTAPI_PORT: int = 8000

    # Milvus
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530

    # LLM
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    class Config:
        env_file = ".env"
        case_sensitive = True

    @field_validator("DB_PORT", "FASTAPI_PORT", "MILVUS_PORT")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """验证端口范围"""
        if not 1 <= v <= 65535:
            raise ValueError(f"端口 {v} 超出有效范围 (1-65535)")
        return v

    @field_validator("DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """验证字符串字段不为空"""
        if not v or not v.strip():
            raise ValueError(f"字段 {cls.__name__} 不能为空")
        return v.strip()

    @field_validator("OPENAI_API_KEY")
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        """验证 OpenAI API Key"""
        if v and not v.strip():
            raise ValueError("OPENAI_API_KEY 不能为空")
        return v.strip()

    @model_validator(mode='after')
    def validate_required_fields(self) -> 'Settings':
        """验证必填字段是否存在"""
        if not self.OPENAI_API_KEY:
            print("Warning: OPENAI_API_KEY 未设置，LLM 功能将不可用", file=sys.stderr)
        return self

settings = Settings()
