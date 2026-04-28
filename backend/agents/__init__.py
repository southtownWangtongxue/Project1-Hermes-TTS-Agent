"""
Agent 模块初始化

提供 LangGraph agent 的核心定义和状态管理。
"""

__version__ = "0.1.0"

from .state import AgentState
from .router import route_intent, route_sensitive_operation

__all__ = [
    "AgentState",
    "route_intent",
    "route_sensitive_operation",
]
