"""
API 基础测试（不依赖数据库和 LLM）
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.security import (
    create_access_token,
    verify_access_token,
    create_admin_token,
    verify_admin_token,
    hash_password,
    verify_password,
    generate_api_key,
    verify_api_key,
)


# ═══════════════════════════════════════════════════════════
# API 端点测试
# ═══════════════════════════════════════════════════════════


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


# ═══════════════════════════════════════════════════════════
# 鉴权模块测试
# ═══════════════════════════════════════════════════════════


class TestJWTToken:
    """JWT Token 生成与验证测试"""

    def test_create_and_verify_access_token(self):
        """访问令牌生成后应能正常验证"""
        token = create_access_token("user-001")
        payload = verify_access_token(token)
        assert payload is not None
        assert payload["sub"] == "user-001"
        assert payload["type"] == "access"

    def test_verify_invalid_token(self):
        """无效令牌应返回 None"""
        payload = verify_access_token("invalid-token-string")
        assert payload is None

    def test_verify_empty_token(self):
        """空令牌应返回 None"""
        payload = verify_access_token("")
        assert payload is None

    def test_admin_token(self):
        """管理员令牌 type 应为 admin"""
        token = create_admin_token()
        is_admin = verify_admin_token(token)
        assert is_admin is True

    def test_access_token_not_admin(self):
        """普通访问令牌不应被识别为管理员"""
        token = create_access_token("user-001")
        is_admin = verify_admin_token(token)
        assert is_admin is False

    def test_expired_token(self):
        """过期令牌验证应返回 None"""
        # 创建一个已过期的 token（过期时间为 -1 分钟）
        token = create_access_token("user-001", expires_minutes=-1)
        payload = verify_access_token(token)
        assert payload is None


class TestPasswordHashing:
    """密码哈希与验证测试"""

    def test_hash_and_verify(self):
        """哈希后验证应通过"""
        hashed = hash_password("my-secret-password")
        assert verify_password("my-secret-password", hashed) is True

    def test_wrong_password(self):
        """错误密码验证应失败"""
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_hash_is_not_plaintext(self):
        """哈希值不应包含明文密码"""
        hashed = hash_password("secret123")
        assert "secret123" not in hashed

    def test_same_password_different_hashes(self):
        """相同密码两次哈希结果应不同（随机盐值）"""
        h1 = hash_password("same-password")
        h2 = hash_password("same-password")
        assert h1 != h2
        # 但都能正确验证
        assert verify_password("same-password", h1)
        assert verify_password("same-password", h2)


class TestAPIKey:
    """API Key 生成与验证测试"""

    def test_generate_and_verify(self):
        """生成的 API Key 应能通过验证"""
        raw, hashed = generate_api_key()
        assert len(raw) == 64  # 32 bytes hex = 64 chars
        assert verify_api_key(raw, hashed) is True

    def test_wrong_api_key(self):
        """错误的 API Key 验证应失败"""
        raw, hashed = generate_api_key()
        wrong_key = "a" * 64
        assert verify_api_key(wrong_key, hashed) is False

    def test_api_key_uniqueness(self):
        """每次生成的 API Key 应不同"""
        raw1, hash1 = generate_api_key()
        raw2, hash2 = generate_api_key()
        assert raw1 != raw2
        assert hash1 != hash2
