"""
LangGraph 全局状态定义

定义 Agent 工作流中所有节点共享的全局状态结构，
基于 TypedDict 实现类型安全的状态传递。
"""
from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Agent 工作流的全局状态

    贯穿整个 LangGraph 流程，各节点通过读写该状态来协作完成
    "用户问题 -> 表结构分析 -> SQL 生成 -> 安全检查 -> 执行 -> 分析" 的完整链路。
    """

    # ── 输入 ──────────────────────────────────────────
    # 用户原始自然语言问题
    user_question: str

    # ── 对话历史 ──────────────────────────────────────
    # 多轮对话消息历史，使用 add_messages 归并器自动追加新消息
    messages: Annotated[list, add_messages]

    # ── Orchestrator 产出 ─────────────────────────────
    # 用户意图类型: query_data / ask_help / write_data
    intent: str
    # 意图分类的置信度，范围 0.0 ~ 1.0
    intent_confidence: float

    # ── Schema Agent 产出 ─────────────────────────────
    # 格式化的数据库表结构信息字符串（供 LLM 上下文使用）
    schema_info: str
    # 根据用户意图匹配到的相关表名列表
    relevant_tables: list[str]

    # ── SQL Coder 产出 ────────────────────────────────
    # LLM 生成的目标 SQL 语句
    generated_sql: str

    # ── SQL 安全审查产出 ──────────────────────────────
    # SQL 安全分类结果，取值为 "safe"（只读查询）或 "dangerous"（写操作）
    sql_category: str

    # ── SQL 执行产出 ──────────────────────────────────
    # SQL 执行结果，每行为一个字典，键为列名
    query_result: list[dict]
    # 查询结果的列名列表（保持顺序）
    query_columns: list[str]

    # ── 分析 Agent 产出 ───────────────────────────────
    # 基于查询结果的自然语言分析洞察文本
    analysis_text: str
    # ECharts 图表配置 JSON，无图表时为 None
    chart_config: dict | None

    # ── 错误处理 ──────────────────────────────────────
    # 流程中发生的错误信息，无错误时为空字符串
    error_message: str

    # ── 流程控制 ──────────────────────────────────────
    # 当前流程所处的阶段标识，如 "schema_loading" / "sql_generating" / "done"
    stage: str
