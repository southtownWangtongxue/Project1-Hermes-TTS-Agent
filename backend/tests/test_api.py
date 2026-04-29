"""
API 基础测试（不依赖数据库和 LLM）
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    """测试健康检查接口"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


@pytest.mark.asyncio
async def test_chat_no_messages():
    """测试对话接口 — 无用户消息时应返回错误"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat/completions",
            json={"messages": [], "stream": True},
        )
        assert response.status_code == 200
        # SSE 错误事件应包含 error
        content = response.text
        assert "error" in content or "未找到用户消息" in content


@pytest.mark.asyncio
async def test_chat_with_message():
    """测试对话接口 — 有用户消息时正常返回 SSE 流"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "查询所有产品"}],
                "stream": True,
            },
        )
        assert response.status_code == 200
        # 即使数据库连接失败，也应返回 SSE 格式的错误
        content = response.text
        assert "data:" in content


@pytest.mark.asyncio
async def test_approve_invalid_action():
    """测试审批接口 — 非法 action 应被拒绝"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/approve",
            json={"task_id": "test-123", "action": "invalid", "comment": ""},
        )
        assert response.status_code == 422  # Pydantic validation error
