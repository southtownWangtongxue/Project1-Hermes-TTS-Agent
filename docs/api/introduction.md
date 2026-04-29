# API 鉴权说明

> **当前版本（v0.1.0）为开发阶段，尚未接入鉴权系统。** 以下为预留的鉴权设计文档，供后续集成参考。

---

## 鉴权方案（预留）

DataAgent Pro 设计了两层鉴权机制：

### 第一层：用户身份认证

计划使用 **JWT（JSON Web Token）** 方案：

```
请求流程：
1. 用户登录 → POST /api/v1/auth/login → 返回 access_token + refresh_token
2. 后续请求在 Header 中携带：Authorization: Bearer <access_token>
3. access_token 过期后使用 refresh_token 刷新
```

### 第二层：操作权限控制

基于角色的访问控制（RBAC）：

| 角色 | 权限 |
|------|------|
| **普通用户** | 发起自然语言查询、查看结果、导出报表 |
| **审批管理员** | 查看待审批任务、通过/驳回写操作 |
| **超级管理员** | 管理数据源、配置知识库、管理用户 |

### 待实现接口

```
POST /api/v1/auth/login        # 用户登录
POST /api/v1/auth/refresh      # 刷新 Token
POST /api/v1/auth/logout       # 用户登出
GET  /api/v1/auth/me           # 获取当前用户信息
```

---

## 当前版本说明

在 v0.1.0 开发版本中，所有 API 接口无需鉴权即可访问。依赖注入函数 `deps.py` 中预留了鉴权钩子：

```python
# backend/app/api/deps.py（示意）

async def get_current_user(
    authorization: str = Header(None)
) -> Optional[User]:
    """
    获取当前用户（当前版本跳过鉴权，直接返回匿名用户）。

    TODO: 接入 JWT 验证后，此函数将：
    1. 解析 Authorization Header 中的 Bearer Token
    2. 验证 Token 有效性和过期时间
    3. 从数据库加载用户信息及角色
    """
    # 占位实现：返回匿名用户
    return User(id="anonymous", role="user")
```

---

## 下一步

- 查看[对话与审批接口](./chat-api.md)了解核心 API 参数
- 查看[安全机制](../advanced/security.md)了解审批流设计
