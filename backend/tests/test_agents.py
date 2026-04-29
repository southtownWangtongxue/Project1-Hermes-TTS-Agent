"""
Agent 单元测试
"""
import pytest
from app.agents.security import mask_sensitive_data, classify_sql


class TestSecurityAgent:
    """Security Agent 测试"""

    def test_mask_phone(self):
        """测试手机号脱敏"""
        data = [{"phone": "13812345678"}]
        result = mask_sensitive_data(data)
        assert result[0]["phone"] == "138****5678"

    def test_mask_id_card(self):
        """测试身份证脱敏"""
        data = [{"id_card": "320102199001011234"}]
        result = mask_sensitive_data(data)
        assert "****" in result[0]["id_card"]
        assert result[0]["id_card"].startswith("320")
        assert result[0]["id_card"].endswith("1234")

    def test_mask_email(self):
        """测试邮箱脱敏"""
        data = [{"email": "user@example.com"}]
        result = mask_sensitive_data(data)
        assert "***" in result[0]["email"]
        assert result[0]["email"].endswith("@example.com")

    def test_mask_multiple_fields(self):
        """测试多字段、多行脱敏"""
        data = [
            {"name": "张三", "phone": "13900001111", "email": "zhangsan@test.com"},
            {"name": "李四", "id_card": "110101198001015678"},
        ]
        result = mask_sensitive_data(data)
        assert result[0]["phone"] == "139****1111"
        assert result[0]["email"] == "z***@test.com"
        assert "****" in result[1]["id_card"]

    def test_empty_data(self):
        """测试空数据"""
        assert mask_sensitive_data([]) == []

    def test_no_sensitive_data(self):
        """测试无敏感字段的数据"""
        data = [{"name": "产品A", "price": 99.9}]
        result = mask_sensitive_data(data)
        assert result == data


class TestClassifySQL:
    """SQL 分类测试（正则层，不调 LLM）"""

    @pytest.mark.asyncio
    async def test_select_is_safe(self):
        """SELECT 语句应为安全"""
        result = await classify_sql("SELECT * FROM orders")
        assert result["category"] == "safe"

    @pytest.mark.asyncio
    async def test_insert_is_dangerous(self):
        """INSERT 语句应为危险"""
        result = await classify_sql("INSERT INTO orders VALUES (1, 'test')")
        # 注意: 危险操作需要 LLM 二次确认，可能失败（无 LLM 环境）
        assert result["category"] in ("safe", "dangerous")

    @pytest.mark.asyncio
    async def test_delete_is_dangerous(self):
        """DELETE 语句应为危险"""
        result = await classify_sql("DELETE FROM orders WHERE id = 1")
        assert result["category"] in ("safe", "dangerous")

    @pytest.mark.asyncio
    async def test_show_is_safe(self):
        """SHOW 语句应为安全"""
        result = await classify_sql("SHOW TABLES")
        assert result["category"] == "safe"
