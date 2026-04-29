# 安全机制与审批流

DataAgent Pro 以 **"读数据随意，改数据必批"** 为核心安全原则，通过多层安全机制保障业务数据安全。

---

## 安全架构总览

```
用户输入自然语言
      │
      ▼
┌─────────────┐
│  SQL Coder   │  生成 SQL
└──────┬──────┘
       ▼
┌─────────────────────────────────────┐
│       Security Agent 双重审计        │
│  ┌──────────┐     ┌──────────┐      │
│  │ 正则快速筛 │ ──→ │ LLM 精判  │      │
│  └──────────┘     └──────────┘      │
└──────────────┬──────────────────────┘
               ▼
      ┌────────┴────────┐
      ▼                 ▼
  ┌───────┐       ┌──────────┐
  │ SELECT │       │ INSERT    │
  │ (读)   │       │ UPDATE    │
  │ 自动   │       │ DELETE    │
  │ 执行   │       │ DROP 等   │
  └───┬───┘       │ (写/DDL)  │
      ▼           │ 触发审批  │
  ┌──────────┐    └─────┬────┘
  │ 数据脱敏  │          ▼
  │ (结果)   │    ┌──────────┐
  └────┬─────┘    │ Graph 中断│
       ▼          │ 推送审批  │
  ┌──────────┐    └─────┬────┘
  │ 返回用户  │          ▼
  └──────────┘    ┌──────────────┐
                  │ 管理员审批    │
                  │ 通过 → 执行  │
                  │ 驳回 → 拒绝  │
                  └──────────────┘
```

---

## 双层 SQL 审计

### 第一层：正则快速筛

用正则表达式快速判断 SQL 的操作类型，作为第一道防线：

```python
import re

# 写操作关键词匹配
WRITE_PATTERNS = [
    r'\bINSERT\s+INTO\b',
    r'\bUPDATE\b',
    r'\bDELETE\s+FROM\b',
    r'\bDROP\s+(TABLE|DATABASE|INDEX)\b',
    r'\bALTER\s+(TABLE|DATABASE)\b',
    r'\bTRUNCATE\b',
    r'\bCREATE\s+(TABLE|DATABASE|INDEX)\b',
    r'\bGRANT\b',
    r'\bREVOKE\b',
]

def regex_classify(sql: str) -> str:
    """正则快速分类 SQL"""
    sql_upper = sql.upper()
    for pattern in WRITE_PATTERNS:
        if re.search(pattern, sql_upper):
            return "write"
    return "read"
```

### 第二层：LLM 精判

正则可能产生误判（如注释中包含 "DELETE" 字样的 SELECT 语句），因此需要 LLM 做语义二次确认：

```python
async def llm_classify(sql: str) -> dict:
    """LLM 语义分析 SQL 风险等级"""
    prompt = f"""
    请分析以下 SQL 语句的操作类型和风险等级。

    SQL:
    ```
    {sql}
    ```

    请返回 JSON：
    {{
      "operation_type": "read/write/dangerous",
      "risk_level": "low/medium/high/critical",
      "reason": "分析理由",
      "tables_affected": ["表名列表"]
    }}

    分类标准：
    - read: 仅 SELECT 查询，不修改数据
    - write: INSERT / UPDATE / DELETE 等修改数据的操作
    - dangerous: DROP / TRUNCATE / ALTER 等结构变更操作
    """
    response = await llm.invoke(prompt)
    return parse_classification(response)
```

### 双重判定逻辑

```python
def classify_sql(sql: str) -> SecurityResult:
    """综合双层判定 SQL 安全等级"""
    # 第一层：正则快速筛
    regex_risk = regex_classify(sql)

    if regex_risk == "read":
        # 正则判定为读，不调用 LLM（节省资源）
        return SecurityResult(risk_level="read", audit_comment="正则判定为只读查询")

    # 第二层：LLM 精判
    llm_result = await llm_classify(sql)

    if llm_result.operation_type == "write":
        return SecurityResult(risk_level="write",
                             audit_comment=llm_result.reason)
    else:
        # LLM 判定实际为只读（正则误判），放行
        return SecurityResult(risk_level="read",
                             audit_comment="LLM 判定为只读查询（正则误判已纠正）")
```

---

## 数据脱敏

在返回查询结果给用户之前，对敏感字段进行脱敏处理。

### 脱敏规则

| 字段类型 | 匹配规则 | 脱敏方式 | 示例 |
|---------|---------|---------|------|
| 手机号 | `1[3-9]\d{9}` | 中间 4 位打码 | `138****1234` |
| 身份证号 | `\d{17}[\dXx]` | 保留前 6 后 4 位 | `320100********1234` |
| 邮箱 | `[\w.-]+@[\w.-]+` | 用户名部分打码 | `abc***@example.com` |
| 银行卡号 | `\d{16,19}` | 保留后 4 位 | `****1234` |

### 实现

```python
# backend/app/core/security.py

import re

MASK_RULES = [
    {
        "name": "手机号",
        "pattern": re.compile(r'(1[3-9]\d)\d{4}(\d{4})'),
        "replacement": r'\1****\2',
        "fields": ["phone", "mobile", "tel", "telephone", "contact"]
    },
    {
        "name": "身份证",
        "pattern": re.compile(r'(\d{6})\d{8}(\d{4})'),
        "replacement": r'\1********\2',
        "fields": ["id_card", "id_number", "identity", "idcard"]
    },
    {
        "name": "邮箱",
        "pattern": re.compile(r'([\w.-]{3})[\w.-]*(@[\w.-]+)'),
        "replacement": r'\1***\2',
        "fields": ["email", "mail", "e_mail"]
    },
]

def mask_sensitive_data(columns: list, rows: list) -> list:
    """对查询结果中的敏感字段进行脱敏"""
    masked_rows = []
    for row in rows:
        masked_row = {}
        for col_name, value in row.items():
            if value and isinstance(value, str):
                for rule in MASK_RULES:
                    if col_name.lower() in rule["fields"]:
                        value = rule["pattern"].sub(rule["replacement"], value)
                        break
            masked_row[col_name] = value
        masked_rows.append(masked_row)
    return masked_rows
```

---

## 审批流配置

### 审批触发条件

在 `backend/app/core/config.py` 中配置审批流行为：

```python
APPROVAL_CONFIG = {
    # 需要审批的操作类型
    "require_approval_for": ["write", "dangerous"],

    # 审批超时时间（秒）
    "approval_timeout": 3600,  # 1 小时

    # 超时后的默认行为
    "timeout_action": "reject",  # reject / auto_approve

    # 白名单：特定表/操作的审批豁免
    "approval_whitelist": {
        "tables": [],  # 例如 ["audit_log"] 审计日志表可豁免
        "users": [],   # 特定用户可豁免审批
    },

    # 审批通知方式（预留）
    "notify_channels": ["web", "wechat_work"],  # 网页 + 企业微信
}
```

### 审批流状态机

```
  ┌──────┐          ┌─────────┐         ┌──────────┐
  │ idle │ ────────→│ pending │────────→│ approved │──→ 执行 SQL
  └──────┘  写操作   └────┬────┘  通过    └──────────┘
                          │
                          │ 驳回
                          ▼
                     ┌──────────┐
                     │ rejected │──→ 通知用户，不执行
                     └──────────┘
```

---

## 并发限流

防止单个用户过度消耗 LLM 资源：

```python
# FastAPI 中间件 — 基于 Redis 的滑动窗口限流
from fastapi import Request, HTTPException
import redis
import time

RATE_LIMIT_CONFIG = {
    "window_size": 60,     # 窗口大小（秒）
    "max_requests": 10,    # 每窗口最多请求数
}

async def rate_limit_middleware(request: Request, call_next):
    user_id = request.headers.get("X-User-ID", "anonymous")
    redis_key = f"rate_limit:{user_id}"
    current_count = redis_client.incr(redis_key)
    if current_count == 1:
        redis_client.expire(redis_key, RATE_LIMIT_CONFIG["window_size"])
    if current_count > RATE_LIMIT_CONFIG["max_requests"]:
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
    return await call_next(request)
```

---

## 安全最佳实践

1. **数据库专用账号**：为 DataAgent 创建最小权限的只读账号
2. **网络隔离**：数据库部署在内网，仅后端服务可访问
3. **日志审计**：记录所有 SQL 执行日志（执行人、时间、SQL 内容、结果）
4. **定期审查**：定期审查审批日志，发现异常访问模式
5. **敏感数据不落盘**：查询缓存仅在 Redis 中存储，不持久化到磁盘
6. **环境变量管理**：密码、API Key 等敏感信息通过 `.env` 管理，不提交到 Git
