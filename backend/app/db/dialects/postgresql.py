"""
PostgreSQL 方言配置
"""
POSTGRESQL_DIALECT_CONFIG = {
    "name": "postgresql",
    "db_type": "postgresql",
    "driver": "asyncpg",
    "connection_template": "postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}",
    # SQL 生成提示
    "llm_prompt_notes": [
        "使用 PostgreSQL 15 语法",
        "字符串使用单引号",
        "LIMIT 用于限制结果数",
        "使用 NOW() 获取当前时间",
        "使用 TO_CHAR() 格式化日期",
        "使用 COALESCE() 处理空值",
        "日期类型转换使用 ::date, ::timestamp",
        "使用 ILIKE 进行不区分大小写的模糊匹配",
    ],
    # 常用函数映射
    "function_aliases": {
        "ifnull": "COALESCE",
        "sysdate": "CURRENT_TIMESTAMP",
    },
}
