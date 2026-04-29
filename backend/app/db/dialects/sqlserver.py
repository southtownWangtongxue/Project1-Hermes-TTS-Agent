"""
SQL Server 方言配置
"""
SQLSERVER_DIALECT_CONFIG = {
    "name": "sqlserver",
    "db_type": "mssql",
    "driver": "aioodbc",
    "connection_template": "mssql+aioodbc://{user}:{password}@{host}:{port}/{database}?driver=ODBC+Driver+18+for+SQL+Server",
    # SQL 生成提示
    "llm_prompt_notes": [
        "使用 SQL Server T-SQL 语法",
        "字符串使用单引号，标识符使用方括号 [table_name]",
        "使用 TOP N 限制结果数（非 LIMIT）",
        "使用 GETDATE() 获取当前时间",
        "使用 CONVERT() 或 FORMAT() 格式化日期",
        "使用 ISNULL() 处理空值",
        "日期计算使用 DATEADD(), DATEDIFF()",
    ],
    # 常用函数映射
    "function_aliases": {
        "limit": "TOP",
        "now": "GETDATE",
        "ifnull": "ISNULL",
        "coalesce": "COALESCE",
    },
}
