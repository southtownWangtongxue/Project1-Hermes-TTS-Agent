"""
Oracle 方言配置
"""
ORACLE_DIALECT_CONFIG = {
    "name": "oracle",
    "db_type": "oracle",
    "driver": "oracledb",
    "connection_template": "oracle+oracledb://{user}:{password}@{host}:{port}/{service_name}",
    # SQL 生成提示
    "llm_prompt_notes": [
        "使用 Oracle 19c 语法",
        "字符串使用单引号",
        "使用 ROWNUM 或 FETCH FIRST N ROWS ONLY 限制结果数",
        "使用 SYSDATE 获取当前时间",
        "使用 TO_CHAR()、TO_DATE() 进行类型转换",
        "使用 NVL() 处理空值",
        "使用 DECODE() 或 CASE WHEN 做条件判断",
        "Oracle 没有 LIMIT，用 ROWNUM <= N",
    ],
    # 常用函数映射
    "function_aliases": {
        "limit": "FETCH FIRST",
        "now": "SYSDATE",
        "ifnull": "NVL",
        "coalesce": "COALESCE",
        "date_format": "TO_CHAR",
        "to_date": "TO_DATE",
    },
}
