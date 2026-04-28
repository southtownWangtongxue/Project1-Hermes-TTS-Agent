from typing import Optional
from pydantic import BaseModel, Field

# Session 相关
class SessionBase(BaseModel):
    session_id: str
    user_id: str
    messages: Optional[list] = []

class SessionCreate(SessionBase):
    pass

class Session(SessionBase):
    id: int
    created_at: str

    class Config:
        from_attributes = True

# User 相关
class UserBase(BaseModel):
    username: str
    full_name: str
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: str

    class Config:
        from_attributes = True

# Approval Request 相关
class ApprovalRequestBase(BaseModel):
    sql: str
    operation_type: str
    target_table: str
    estimated_rows: int
    risk_level: str
    created_by: str
    status: str = 'pending'

class ApprovalRequestCreate(ApprovalRequestBase):
    pass

class ApprovalRequest(ApprovalRequestBase):
    id: int
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True

class ApprovalStatus(str):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
