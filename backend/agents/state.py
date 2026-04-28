"""
Agent 状态定义

定义 LangGraph 状态机的状态结构，支持用户输入、意图分类、RAG 检索、SQL 生成、验证、审批等全流程状态管理。
"""

from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    Agent 状态定义

    该状态对象贯穿整个 LangGraph 状态机，包含用户输入、意图分类、RAG 检索、SQL 生成、验证、审批和结果分析等所有流程的状态。

    使用说明:
    - 使用 add_messages 函数处理消息列表，确保历史对话正确累积
    - 必填字段: user_query, session_id, user_id
    - 可选字段: 大部分字段都有默认值，可以直接初始化
    """

    # ==================== 用户输入信息 ====================
    user_query: str
    """用户的原始查询文本"""
    session_id: str
    """当前会话的唯一标识符"""
    user_id: str
    """当前用户的唯一标识符"""

    # ==================== 意图分类结果 ====================
    intent: Literal["query", "approval", "general"]
    """意图分类结果: query-查询、approval-审批、general-通用对话"""
    is_sensitive_operation: bool = False
    """是否为敏感操作（需要人工审批的操作）"""

    # ==================== RAG 检索结果 ====================
    rag_context: str = ""
    """从向量数据库检索到的相关上下文信息"""

    # ==================== SQL 生成结果 ====================
    sql: str = ""
    """生成的 SQL 查询语句"""
    sql_confidence: float = 0.0
    """SQL 生成的置信度（0.0-1.0）"""

    # ==================== SQL 验证结果 ====================
    is_valid: bool = True
    """SQL 是否通过验证"""
    validation_error: str = ""
    """验证错误信息（如果验证失败）"""

    # ==================== 审批结果 ====================
    approval_status: Literal["pending", "approved", "rejected"] = "pending"
    """审批状态: pending-待审批、approved-已批准、rejected-已拒绝"""
    approval_request_id: str = ""
    """审批请求的唯一标识符"""

    # ==================== 数据库查询结果 ====================
    query_result: list = []
    """数据库查询返回的结果数据（列表形式）"""
    query_columns: list = []
    """查询结果的列名列表"""

    # ==================== 分析结果 ====================
    summary: str = ""
    """查询结果的自然语言总结"""
    chart_type: str = ""
    """建议的图表类型（用于可视化）"""

    # ==================== 历史对话 ====================
    messages: Annotated[list, add_messages]
    """对话历史消息列表，自动管理消息累积"""
