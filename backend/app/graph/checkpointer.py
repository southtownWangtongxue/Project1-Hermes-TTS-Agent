"""
Redis 状态快照持久化

用于 LangGraph Human-in-the-loop 中断时保存和恢复 Graph 状态。
将 AgentState 序列化为 JSON 存入 Redis，以 thread_id 为键。
"""
import json

import redis.asyncio as aioredis

from app.core.config import settings

# ── Redis 异步客户端 ──────────────────────────────────
# 全局单例，所有 checkpoint 操作复用同一个连接
redis_client = aioredis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)

# checkpoint 在 Redis 中的 key 前缀
CHECKPOINT_KEY_PREFIX = "graph:checkpoint"
# checkpoint 默认过期时间（秒）
CHECKPOINT_TTL = 3600  # 1 小时


async def save_checkpoint(thread_id: str, state: dict) -> None:
    """保存 Graph 状态快照到 Redis

    将 AgentState 字典序列化为 JSON 后存入 Redis，
    并设置过期时间防止内存泄漏。

    参数:
        thread_id: 对话线程 ID，作为 Redis key 的一部分
        state: AgentState 字典，将序列化为 JSON 存储
    """
    key = f"{CHECKPOINT_KEY_PREFIX}:{thread_id}"
    payload = json.dumps(state, ensure_ascii=False, default=str)
    await redis_client.set(key, payload)
    await redis_client.expire(key, CHECKPOINT_TTL)


async def load_checkpoint(thread_id: str) -> dict | None:
    """从 Redis 加载 Graph 状态快照

    根据 thread_id 查找并反序列化之前保存的状态。

    参数:
        thread_id: 对话线程 ID

    返回:
        反序列化的状态字典；若 key 不存在或已过期则返回 None
    """
    key = f"{CHECKPOINT_KEY_PREFIX}:{thread_id}"
    data = await redis_client.get(key)
    if data is None:
        return None
    return json.loads(data)


async def delete_checkpoint(thread_id: str) -> None:
    """删除 Graph 状态快照

    用于清理已完成或已取消的对话状态。

    参数:
        thread_id: 对话线程 ID
    """
    key = f"{CHECKPOINT_KEY_PREFIX}:{thread_id}"
    await redis_client.delete(key)


async def checkpoint_exists(thread_id: str) -> bool:
    """检查指定 thread_id 的 checkpoint 是否存在

    参数:
        thread_id: 对话线程 ID

    返回:
        True 表示存在有效 checkpoint，False 表示不存在或已过期
    """
    key = f"{CHECKPOINT_KEY_PREFIX}:{thread_id}"
    return await redis_client.exists(key) > 0
