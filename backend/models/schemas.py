from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# Session 相关
class SessionBase(BaseModel):
    """会话基础模型"""
    session_id: str
    user_id: str
    messages: Optional[List] = None  # 修复：使用 None 而非空列表


class SessionCreate(SessionBase):
    """会话创建模型"""
    pass


class SessionSchema(SessionBase):
    """会话模型（ORM）"""
    id: int
    created_at: str

    class Config:
        from_attributes = True


# User 相关
class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    full_name: str
    is_active: bool = True


class UserCreate(UserBase):
    """用户创建模型"""
    password: str


class User(UserBase):
    """用户模型（ORM）"""
    id: int
    created_at: str

    class Config:
        from_attributes = True


# Approval Request 相关
class ApprovalRequestBase(BaseModel):
    """审批请求基础模型"""
    sql: str
    operation_type: str
    target_table: str
    estimated_rows: int
    risk_level: str
    created_by: str
    status: str = 'pending'

    @field_validator('operation_type')
    @classmethod
    def validate_operation_type(cls, v: str) -> str:
        """验证操作类型是否有效"""
        valid_operations = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'TRUNCATE']
        if v.upper() not in valid_operations:
            raise ValueError(f'operation_type must be one of: {", ".join(valid_operations)}')
        return v

    @field_validator('risk_level')
    @classmethod
    def validate_risk_level(cls, v: str) -> str:
        """验证风险等级是否有效"""
        valid_levels = ['low', 'medium', 'high']
        if v.lower() not in valid_levels:
            raise ValueError(f'risk_level must be one of: {", ".join(valid_levels)}')
        return v


class ApprovalRequestCreate(ApprovalRequestBase):
    """审批请求创建模型"""
    pass


class ApprovalRequest(ApprovalRequestBase):
    """审批请求模型（ORM）"""
    id: int
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class ApprovalStatus(str):
    """审批状态枚举"""
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'

    @classmethod
    def values(cls) -> List[str]:
        """获取所有有效状态值"""
        return [cls.PENDING, cls.APPROVED, cls.REJECTED]
