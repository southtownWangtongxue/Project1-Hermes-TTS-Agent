"""
意图路由节点

提供意图分类和敏感操作检测功能，用于区分普通查询操作和需要人工审批的操作。
"""

from typing import Literal
from .state import AgentState


def route_intent(state: AgentState) -> Literal["query", "approval"]:
    """
    意图路由：区分查询操作和审批操作

    检测 SQL 中是否包含敏感操作（INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE），
    如果检测到敏感操作，则设置 is_sensitive_operation 标志并返回 "approval" 路由。

    Args:
        state: Agent 状态对象，包含用户查询和生成的 SQL

    Returns:
        str: 路由目标，"query" 表示普通查询操作，"approval" 表示需要审批的操作
    """
    # 检查是否为敏感操作
    sensitive_operations = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]

    for op in sensitive_operations:
        if op in state.sql.upper():
            state.is_sensitive_operation = True
            return "approval"

    return "query"


def route_sensitive_operation(state: AgentState) -> Literal["approver", "query"]:
    """
    敏感操作路由

    根据检测到的敏感操作标志，决定后续路由目标：
    - 如果是敏感操作，路由到 approver 节点
    - 否则，路由到 query_processor 节点

    Args:
        state: Agent 状态对象，包含敏感操作标志

    Returns:
        str: 路由目标，"approver" 表示审批节点，"query" 表示查询处理节点
    """
    if state.is_sensitive_operation:
        return "approver"
    return "query"
