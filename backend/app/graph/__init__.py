"""
graph 包 —— LangGraph 工作流核心模块

提供:
- AgentState: 全局工作流状态定义
- checkpointer: Redis 状态快照持久化（用于 Human-in-the-loop 中断恢复）
"""
from app.graph.state import AgentState
from app.graph.checkpointer import (
    save_checkpoint,
    load_checkpoint,
    delete_checkpoint,
    checkpoint_exists,
)

__all__ = [
    "AgentState",
    "save_checkpoint",
    "load_checkpoint",
    "delete_checkpoint",
    "checkpoint_exists",
]
