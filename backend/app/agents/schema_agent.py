"""
Schema Agent - 元数据专家
根据用户意图动态从业务库加载相关表结构、字段注释
"""
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncEngine


async def get_table_schemas(
    engine: AsyncEngine, table_names: list[str] | None = None
) -> str:
    """
    动态获取数据库表结构信息，返回格式化字符串供 LLM 作为上下文使用。

    参数:
        engine: SQLAlchemy 异步引擎
        table_names: 要获取的表名列表，为 None 时获取所有表

    返回:
        格式化的表结构字符串，示例格式如下：

        表名: orders
        列:
        - id (INTEGER, NOT NULL, 主键) - 订单ID
        - user_id (INTEGER, NOT NULL) - 用户ID
        - amount (DECIMAL(10,2), NOT NULL) - 订单金额
        - created_at (DATETIME) - 创建时间
    """

    def _sync_get_schemas(conn):
        """同步函数：通过 run_sync 在异步上下文中执行。"""
        inspector = inspect(conn)

        # 确定要查询的表列表
        if table_names is None:
            tables = inspector.get_table_names()
        else:
            all_tables = inspector.get_table_names()
            tables = [t for t in table_names if t in all_tables]

        parts: list[str] = []
        for table in tables:
            lines = [f"表名: {table}"]
            lines.append("列:")

            # 获取主键列名集合
            pk_constraint = inspector.get_pk_constraint(table)
            pk_cols: set[str] = set(pk_constraint.get("constrained_columns", []))

            for col in inspector.get_columns(table):
                col_name = col["name"]
                col_type = str(col["type"])
                # 是否可为空
                nullable = "" if col.get("nullable", True) else ", NOT NULL"
                # 是否为主键
                pk_tag = ", 主键" if col_name in pk_cols else ""
                # 默认值
                default = col.get("default")
                default_str = f", 默认值={default}" if default is not None else ""
                # 字段注释
                comment = col.get("comment", "")
                comment_str = f" - {comment}" if comment else ""

                lines.append(
                    f"- {col_name} ({col_type}{nullable}{default_str}{pk_tag}){comment_str}"
                )

            parts.append("\n".join(lines))

        return "\n\n".join(parts) if parts else "（数据库中无用户表）"

    async with engine.connect() as conn:
        return await conn.run_sync(_sync_get_schemas)


async def filter_relevant_tables(
    engine: AsyncEngine, user_intent: str
) -> list[str]:
    """
    根据用户意图匹配相关表名。

    通过关键词匹配：若用户问题中包含某表名（不区分大小写），
    则该表视为相关。若无任何匹配，返回所有表名的前 10 个。

    参数:
        engine: SQLAlchemy 异步引擎
        user_intent: 用户自然语言问题

    返回:
        匹配到的相关表名列表
    """

    def _sync_get_tables(conn):
        inspector = inspect(conn)
        return inspector.get_table_names()

    async with engine.connect() as conn:
        all_tables = await conn.run_sync(_sync_get_tables)

    if not all_tables:
        return []

    user_lower = user_intent.lower()
    relevant = [t for t in all_tables if t.lower() in user_lower]

    if not relevant:
        # 无匹配时返回前 10 个表作为兜底
        return all_tables[:10]

    return relevant
