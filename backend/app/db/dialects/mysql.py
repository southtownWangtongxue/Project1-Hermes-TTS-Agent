"""
MySQL 方言配置
"""
MYSQL_DIALECT_CONFIG = {
    "name": "mysql",
    "db_type": "mysql",
    "driver": "asyncmy",
    "connection_template": "mysql+asyncmy://{user}:{password}@{host}:{port}/{database}",
    # SQL 生成提示
    "llm_prompt_notes": [
        "使用 MySQL 8.0 语法",
        "字符串使用单引号",
        "LIMIT 用于限制结果数",
        "使用 NOW() 获取当前时间",
        "使用 DATE_FORMAT() 格式化日期",
        "使用 IFNULL() 处理空值",
    ],
    # 常用函数映射
    "function_aliases": {
        "length": "CHAR_LENGTH",
        "substr": "SUBSTRING",
    },
}
