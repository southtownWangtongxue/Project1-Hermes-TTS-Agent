# 对话与审批接口

本文档详细描述核心对话接口 `POST /api/v1/chat/completions` 和审批回调接口 `POST /api/v1/chat/approve` 的请求/响应格式及 SSE 事件类型。

---

## POST /api/v1/chat/completions

核心对话接口，接收用户自然语言输入，通过 SSE 流式返回处理结果。

### 请求

**URL**：`/api/v1/chat/completions`

**Method**：`POST`

**Content-Type**：`application/json`

**Accept**：`text/event-stream`

```json
{
  "query": "去年每个月的销售额是多少？",
  "datasource_id": "mysql_main",
  "options": {
    "max_retries": 2,
    "enable_analysis": true,
    "enable_chart": true
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | 是 | 用户的自然语言问题 |
| `datasource_id` | string | 否 | 目标数据源 ID，默认使用 `default` |
| `options.max_retries` | int | 否 | SQL 执行失败最大重试次数，默认 2 |
| `options.enable_analysis` | bool | 否 | 是否启用数据分析（同比/环比/异常检测），默认 true |
| `options.enable_chart` | bool | 否 | 是否生成图表配置，默认 true |

### 响应（SSE 流）

响应格式遵循 SSE 规范，`Content-Type` 为 `text/event-stream`。

每条消息格式：

```
event: <事件类型>
data: <JSON 数据>

```

#### 事件类型详解

##### 1. status — 状态更新

```json
{
  "event": "status",
  "data": {
    "stage": "intent_parsing",
    "message": "正在理解你的问题..."
  }
}
```

**stage 枚举值**：

| stage | 含义 |
|-------|------|
| `intent_parsing` | 意图解析中 |
| `rag_retrieving` | 知识库检索中 |
| `schema_loading` | 加载表结构中 |
| `sql_generating` | 生成 SQL 中 |
| `sql_retrying` | SQL 执行失败，正在重试 |
| `executing` | 执行 SQL 查询中 |
| `analyzing` | 数据分析中 |
| `chart_generating` | 生成图表配置中 |
| `exporting` | 文件导出中 |

##### 2. sql_generation — SQL 生成结果

```json
{
  "event": "sql_generation",
  "data": {
    "sql": "SELECT month, SUM(amount) AS total FROM sales WHERE year = 2024 GROUP BY month ORDER BY month",
    "dialect": "mysql"
  }
}
```

##### 3. result_data — 查询结果

```json
{
  "event": "result_data",
  "data": {
    "columns": ["month", "total"],
    "rows": [
      [1, 150000],
      [2, 180000],
      [3, 120000]
    ],
    "row_count": 3
  }
}
```

##### 4. insights — 分析洞察

```json
{
  "event": "insights",
  "data": {
    "text": "2月销售额达到峰值18万元，环比增长20%。3月出现明显回落至12万元，降幅33.3%。整体呈现先升后降的趋势。"
  }
}
```

##### 5. chart — 图表配置

```json
{
  "event": "chart",
  "data": {
    "echartsConfig": {
      "title": { "text": "2024年月度销售额" },
      "xAxis": { "type": "category", "data": ["1月", "2月", "3月"] },
      "yAxis": { "type": "value" },
      "series": [{
        "type": "bar",
        "data": [150000, 180000, 120000]
      }]
    }
  }
}
```

##### 6. approval_required — 需要审批

```json
{
  "event": "approval_required",
  "data": {
    "task_id": "abc-123-def-456",
    "sql": "UPDATE users SET status = 'inactive' WHERE last_login < '2023-01-01'",
    "risk_level": "write",
    "message": "检测到写操作，需要管理员审批后执行"
  }
}
```

##### 7. approval_result — 审批结果

```json
{
  "event": "approval_result",
  "data": {
    "task_id": "abc-123-def-456",
    "status": "approved",
    "message": "审批已通过，正在执行操作..."
  }
}
```

##### 8. export_ready — 导出就绪

```json
{
  "event": "export_ready",
  "data": {
    "file_url": "/exports/report_20240429.xlsx",
    "file_name": "report_20240429.xlsx",
    "file_size": 10240
  }
}
```

##### 9. error — 错误

```json
{
  "event": "error",
  "data": {
    "stage": "executing",
    "message": "数据库连接超时",
    "detail": "ConnectionError: unable to connect to mysql:3306 after 30s"
  }
}
```

##### 10. done — 完成

```json
{
  "event": "done",
  "data": {
    "message": "分析完成"
  }
}
```

---

## POST /api/v1/chat/approve

管理员审批回调接口，用于对需要审批的写操作进行人工决策。

### 请求

**URL**：`/api/v1/chat/approve`

**Method**：`POST`

**Content-Type**：`application/json`

```json
{
  "task_id": "abc-123-def-456",
  "action": "approve",
  "comment": "确认无误，允许执行"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `task_id` | string | 是 | 审批任务 ID（由 `approval_required` 事件返回） |
| `action` | string | 是 | 审批操作：`approve`（通过）或 `reject`（驳回） |
| `comment` | string | 否 | 审批备注 |

### 响应

**通过时**：

```json
{
  "task_id": "abc-123-def-456",
  "status": "approved",
  "message": "审批通过，SQL 已执行"
}
```

**驳回时**：

```json
{
  "task_id": "abc-123-def-456",
  "status": "rejected",
  "message": "审批已驳回，操作未执行"
}
```

---

## POST /api/v1/chat/stop

中断正在执行的 Agent 任务。

### 请求

```json
{
  "task_id": "abc-123-def-456"
}
```

### 响应

```json
{
  "status": "stopped",
  "message": "任务已中断"
}
```

---

## 完整交互流程示例

### 场景 1：读查询（SELECT）

```
1. 用户发送："查询本月销售额前5的产品"
2. 后端 SSE 流式返回：
   → status: intent_parsing
   → status: rag_retrieving
   → status: schema_loading
   → status: sql_generating
   → sql_generation: { "sql": "SELECT ...", "dialect": "mysql" }
   → status: executing
   → result_data: { "columns": [...], "rows": [...] }
   → status: analyzing
   → insights: { "text": "..." }
   → status: chart_generating
   → chart: { "echartsConfig": {...} }
   → done: { "message": "分析完成" }
```

### 场景 2：写操作（UPDATE）— 含审批

```
1. 用户发送："把过期会员标记为 inactive"
2. 后端 SSE 流式返回：
   → status: intent_parsing
   → ...各种中间阶段...
   → sql_generation: { "sql": "UPDATE members SET status='inactive' WHERE ..." }
   → approval_required: { "task_id": "xxx", "sql": "...", "risk_level": "write" }
   
   [此时 Graph 中断，等待管理员操作]

3. 管理员在前端点击"通过"
4. 前端 POST /api/v1/chat/approve { "task_id": "xxx", "action": "approve" }

5. 后端继续 SSE 流式返回：
   → approval_result: { "status": "approved" }
   → status: executing
   → result_data: { "columns": [...], "rows": [...] }
   → done: { "message": "操作完成" }
```
