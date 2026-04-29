# 工作流与状态机详解

本文档详细描述 LangGraph 工作流的 `AgentState` 字段定义、节点拓扑、Human-in-the-loop 中断/恢复流程以及 SSE 事件流时序。

---

## AgentState 字段定义

`AgentState` 是 LangGraph 全局状态对象，在工作流的各节点间流转。定义于 `backend/app/graph/state.py`：

```python
from typing import TypedDict, List, Optional, Any
from langgraph.graph import MessagesState

class AgentState(MessagesState):
    """全局工作流状态"""

    # === 用户输入 ===
    user_query: str              # 用户原始自然语言问题

    # === 意图解析 ===
    intent: str                  # 意图分类：query / analysis / export / write
    task_plan: List[dict]        # 拆解后的子任务列表

    # === RAG 检索 ===
    rag_context: str             # 检索到的业务规范/指标定义文本

    # === 表结构 ===
    relevant_tables: List[str]   # Schema Agent 筛选出的相关表名
    table_schemas: str           # 相关表的 DDL 信息（精简版）

    # === SQL 生成 ===
    generated_sql: str           # SQL Coder 生成的 SQL
    sql_dialect: str             # 目标数据库方言 (mysql/pg/oracle/sqlserver)
    sql_retry_count: int         # SQL 执行失败重试次数（最多 2 次）

    # === 安全审计 ===
    sql_risk_level: str          # read / write / dangerous
    sql_audit_comment: str       # 审计说明

    # === 执行结果 ===
    query_result: Optional[List[dict]]  # SQL 执行结果（行列表）
    execution_error: Optional[str]      # 执行异常信息

    # === 分析结果 ===
    analysis_insights: str              # Analyst Agent 自然语言洞察
    chart_config: Optional[dict]        # Reporter 生成的 ECharts JSON 配置
    export_file_path: Optional[str]     # 导出文件路径

    # === 审批流 ===
    approval_required: bool             # 是否需要人工审批
    approval_task_id: Optional[str]     # 审批任务 ID
    approval_status: Optional[str]      # pending / approved / rejected

    # === 错误处理 ===
    error_message: Optional[str]        # 全局错误信息
    final_response: str                 # 最终返回给用户的文本
```

---

## 完整 10 节点 Graph 拓扑

工作流由以下节点组成（定义于 `backend/app/graph/workflow.py`）：

| 序号 | 节点函数 | 职责 | 条件边 |
|------|---------|------|--------|
| 1 | `orchestrator_node` | 意图解析、任务拆解 | → RAG |
| 2 | `rag_node` | 检索知识库获取业务规范 | → Schema |
| 3 | `schema_node` | 加载相关表结构 | → SQL Coder |
| 4 | `sql_coder_node` | Text-to-SQL 生成 | → Security |
| 5 | `security_node` | SQL 审计分类 | → Execute (SELECT) 或 Interrupt (写操作) |
| 6 | `execute_node` | 执行 SELECT 查询 | → Analyst / 错误时 → 结束 |
| 7 | `analyst_node` | 数据分析 | → Reporter |
| 8 | `reporter_node` | 生成图表配置 | → 结束 |
| 9 | `interrupt_node` | 挂起工作流，等待人工审批 | → 等待外部 `/approve` 回调 |
| 10 | `approve_handler_node` | 处理审批结果（通过/拒绝） | → Execute 或结束 |

条件边逻辑：

```python
def route_after_security(state: AgentState) -> str:
    """根据安全审计结果路由"""
    if state["sql_risk_level"] == "read":
        return "execute_node"
    else:
        return "interrupt_node"

def route_after_execute(state: AgentState) -> str:
    """根据执行结果路由"""
    if state["execution_error"]:
        return "end"  # 执行失败，终止流程
    return "analyst_node"
```

---

## Human-in-the-loop 中断/恢复流程

### 写操作检测

Security Agent 使用 **正则 + LLM 双重检测** 判断 SQL 类型：

1. **正则快速筛**：匹配 `INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE`
2. **LLM 精判**：提交 SQL 给 LLM 做语义分析，避免正则误判（如注释中的 `DELETE` 字样）

### 中断流程

```
1. Security Agent 检测到写操作
       │
       ▼
2. 调用 graph.interrupt(reason="需要管理员审批")
       │
       ▼
3. LangGraph 自动将当前状态快照保存到 Redis
       │
       ▼
4. 后端返回 SSE 事件: { "event": "approval_required", "task_id": "xxx" }
       │
       ▼
5. 前端展示审批提示，通知管理员
```

### 恢复流程

```
1. 管理员在前端审批页面点击"通过"或"驳回"
       │
       ▼
2. 前端 POST /api/v1/chat/approve
   { "task_id": "xxx", "action": "approve" }
       │
       ▼
3. 后端从 Redis 加载中断快照
       │
       ▼
4. 调用 Command(resume=...) 恢复 Graph 执行
       │
       ▼
5. 审批通过 → 执行 SQL → Analyst → Reporter → SSE 输出
   审批驳回 → 返回驳回信息给用户
```

### 代码示例

```python
# workflow.py — 中断节点
def security_node(state: AgentState) -> AgentState:
    """SQL 安全审计节点"""
    result = classify_sql(state["generated_sql"])

    state["sql_risk_level"] = result.risk_level
    state["sql_audit_comment"] = result.comment

    if result.risk_level != "read":
        # 标记需要审批，Graph 将在此中断
        state["approval_required"] = True

    return state

# chat.py — 审批回调处理
@router.post("/api/v1/chat/approve")
async def handle_approval(task_id: str, action: str):
    graph = get_graph()
    config = {"configurable": {"thread_id": task_id}}

    if action == "approve":
        # 恢复执行
        result = await graph.ainvoke(
            Command(resume={"approved": True}),
            config
        )
    else:
        # 拒绝，注入拒绝信息
        result = await graph.ainvoke(
            Command(resume={"approved": False}),
            config
        )
    return result
```

---

## SSE 事件流时序图

```
用户发送 "去年每个月的销售额"
    │
    ▼
客户端 ←── SSE 连接建立
    │
    ▼
客户端 ←── event: status
           data: {"stage":"intent_parsing","message":"正在理解你的问题..."}
    │
    ▼
客户端 ←── event: status
           data: {"stage":"schema_loading","message":"正在加载表结构..."}
    │
    ▼
客户端 ←── event: sql_generation
           data: {"sql":"SELECT month, SUM(amount) FROM sales WHERE year=2025 GROUP BY month"}
    │
    ▼
客户端 ←── event: status
           data: {"stage":"executing","message":"正在执行查询..."}
    │
    ▼
客户端 ←── event: result_data
           data: {"columns":["month","total"],"rows":[[1,150000],[2,180000],...]}
    │
    ▼
客户端 ←── event: status
           data: {"stage":"analyzing","message":"正在分析数据..."}
    │
    ▼
客户端 ←── event: insights
           data: {"text":"2月销售额环比增长20%，为全年最高月份。3月出现明显回落..."}
    │
    ▼
客户端 ←── event: chart
           data: {"echartsConfig":{...}}  # ECharts 柱状图配置
    │
    ▼
客户端 ←── event: done
           data: {"message":"分析完成"}
```

### 全部 SSE 事件类型

| 事件类型 | 触发时机 | data 内容 |
|---------|---------|----------|
| `status` | 各阶段开始/完成 | `stage`, `message` |
| `sql_generation` | SQL Coder 生成 SQL 后 | `sql`, `dialect` |
| `result_data` | SQL 执行返回结果 | `columns`, `rows`, `row_count` |
| `insights` | Analyst 分析完成 | `text` (自然语言洞察) |
| `chart` | Reporter 生成图表配置 | `echartsConfig` (ECharts JSON) |
| `approval_required` | 检测到写操作，需要审批 | `task_id`, `sql`, `risk_level` |
| `approval_result` | 审批完成 | `status`, `message` |
| `export_ready` | 文件导出完成 | `file_url`, `file_name` |
| `error` | 任意阶段出错 | `stage`, `message`, `detail` |
| `done` | 工作流结束 | `message` |

---

## 审批流生命周期

```
┌────────┐   检测到写操作    ┌────────┐   管理员通过    ┌────────┐
│  idle  │ ────────────────→ │pending │ ─────────────→│approved│
└────────┘                   └────────┘                └────────┘
                                  │ 管理员驳回
                                  ▼
                             ┌────────┐
                             │rejected│
                             └────────┘
```

- **idle**：初始状态，无审批任务
- **pending**：等待管理员审批，Graph 处于中断状态
- **approved**：审批通过，SQL 继续执行
- **rejected**：审批驳回，返回拒绝原因给用户

每个审批任务会在 Redis 中以 `thread_id` 为键保存完整状态快照，审批完成后删除。
