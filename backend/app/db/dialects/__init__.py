"""
SQL 方言配置模块
"""
from app.db.dialects.mysql import MYSQL_DIALECT_CONFIG
from app.db.dialects.postgresql import POSTGRESQL_DIALECT_CONFIG
from app.db.dialects.sqlserver import SQLSERVER_DIALECT_CONFIG
from app.db.dialects.oracle import ORACLE_DIALECT_CONFIG

# 方言名称到配置的映射字典
DIALECT_MAP = {
    "mysql": MYSQL_DIALECT_CONFIG,
    "postgresql": POSTGRESQL_DIALECT_CONFIG,
    "sqlserver": SQLSERVER_DIALECT_CONFIG,
    "oracle": ORACLE_DIALECT_CONFIG,
}


def get_dialect_config(dialect_name: str) -> dict:
    """根据方言名称获取配置，未知方言默认返回 MySQL"""
    return DIALECT_MAP.get(dialect_name.lower(), MYSQL_DIALECT_CONFIG)


def get_llm_prompt_notes(dialect_name: str) -> str:
    """获取 LLM SQL 生成的方言提示文本"""
    config = get_dialect_config(dialect_name)
    notes = config.get("llm_prompt_notes", [])
    return "\n".join(f"- {note}" for note in notes)


def list_supported_dialects() -> list[str]:
    """列出所有支持的方言名称"""
    return list(DIALECT_MAP.keys())


__all__ = [
    "MYSQL_DIALECT_CONFIG",
    "POSTGRESQL_DIALECT_CONFIG",
    "SQLSERVER_DIALECT_CONFIG",
    "ORACLE_DIALECT_CONFIG",
    "DIALECT_MAP",
    "get_dialect_config",
    "get_llm_prompt_notes",
    "list_supported_dialects",
]
