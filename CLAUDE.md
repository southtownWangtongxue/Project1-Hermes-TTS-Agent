# CLAUDE.md
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**DataAgent Pro** — an intelligent business data interaction platform that enables non-technical users to query, analyze, and visualize business data via natural language (Text-to-SQL), powered by a Multi-Agent collaborative architecture.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend framework | Python 3.10+, FastAPI (async, SSE streaming) |
| Agent orchestration | LangGraph 1.x (stateful workflows, Human-in-the-loop) |
| Agent framework | LangChain 1.x (tools, output parsers), deepAgents 0.5.x (structured reasoning) |
| Frontend | Vue 3 + Vite + Element Plus + Echarts |
| ORM / DB driver | SQLAlchemy (multi-dialect: MySQL, PostgreSQL, SQL Server, Oracle) |
| Vector DB | Milvus 2.x (RAG knowledge base) |
| Cache / State | Redis (Graph interrupt state snapshots) |
| LLM | Privately deployed Qwen or GLM models |
| Deployment | Docker Compose (dev), Kubernetes (prod), Nginx (static frontend) |
| Documentation | VitePress (must be delivered as deployable online docs in `docs/`) |

## Multi-Agent Architecture (Hermes Pattern)

The system follows a **Control Plane + Data Plane + Expert Workers** architecture:

1. **Orchestrator Agent** — intent parsing, task decomposition, LangGraph state management, dynamic routing
2. **Misc Agent** — handles non-professional/general questions (杂项节点), prevents non-data questions from polluting the main pipeline
3. **RAG Agent** — retrieves operational standards and metric definitions from Milvus
4. **Schema Agent** — dynamically loads relevant table schemas, filters irrelevant tables to reduce token cost
5. **SQL Coder Agent** — generates dialect-specific SQL (MySQL/PG/Oracle/SQL Server), self-corrects on execution errors (max 2 retries)
6. **Security Agent** — classifies SQL as read (SELECT → allow) or write (INSERT/UPDATE/DELETE/DROP → block, trigger human approval)
7. **Analyst Agent** — performs statistical analysis (YoY, MoM, anomaly detection) on query results
8. **Reporter Agent** — generates Echarts JSON configs for visualization, or Excel/CSV file export

## Core Workflow

```
User Input → Intent Routing
  ├─ ask_help / non-data → Misc Agent → Stream output
  └─ query_data / write_data → Schema Agent → SQL Coder → Security Agent
        ├─ SELECT → Execute SQL → Analyst Agent → Reporter Agent → Stream output
        └─ DML/DDL → Suspend Graph → Push approval → Admin approve/reject → Resume or reject
```

The workflow is implemented as a **LangGraph 1.x state graph** with interrupt/resume for Human-in-the-loop. Graph state is persisted to Redis via `checkpointer.py` with a default TTL of **1 hour**. The state schema is defined in `app/graph/state.py` (AgentState TypedDict).

## Key API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v1/chat/completions` | Core chat (SSE streaming: text, chart config, intermediate state) |
| `POST` | `/api/v1/chat/approve` | Admin approval callback (task_id + action: approve/reject) |
| `POST` | `/api/v1/chat/stop` | Interrupt agent execution |
| `GET` | `/api/v1/datasource/list` | List user-accessible data sources |
| `POST` | `/api/v1/export/excel` | Async export to Excel/CSV |

## 开发命令速查

```bash
# === 后端 ===
cd backend
uv sync --group dev              # 安装/同步依赖（含 dev）
uv run data-agent                # 启动后端 (uvicorn, 端口 8000, 热重载)
uv run uvicorn app.main:app --reload --port 8000  # 等效命令
uv run pytest                    # 运行全部测试
uv run pytest -k "test_name"     # 运行匹配名称的单个测试
uv run pytest tests/test_agents.py::TestSecurityAgent::test_mask_phone  # 运行指定测试函数

# === 前端 ===
cd frontend
npm install                      # 安装依赖
npm run dev                      # 启动开发服务器 (端口 5173)
npm run build                    # 生产构建
npx vue-tsc --noEmit             # TypeScript 类型检查

# === 基础设施 ===
cp .env.example .env             # 创建环境变量文件（按需修改 LLM Key 和 DB 密码）
docker-compose up -d             # 启动所有服务 (Redis+etcd+MinIO+Milvus+MySQL+PostgreSQL)
docker-compose ps                # 查看服务状态
docker-compose down -v           # 停止并清理所有服务（含数据卷）
./scripts/start-dev.sh           # 一键启动开发环境

# === 文档 ===
cd docs
npm install                      # 安装 VitePress 依赖
npm run docs:dev                 # 启动文档开发服务器
npm run docs:build               # 构建静态文档站点
```

## Known Issues (待修复)

从 DEVELOPMENT_PLAN.md 阶段 2 遗留（记录于 2026-04-29）：

| # | 问题 | 优先级 |
|---|------|--------|
| 1 | schema/sql_coder 节点缺少错误短路条件边，错误传播链路过长 | 高 |
| 2 | chat.py 中 GraphInterrupt 用字符串匹配捕获，应改为 `except GraphInterrupt` | 高 |
| 3 | execute_node 丢失 Phase1 的 SQL 自纠错重试能力 | 中 |

## Important Constraints
- 在Python项目测试时，确保项目在虚拟环境中使用uv安装项目依赖进行测试
- **"读数据随意，改数据必批"** — reads are free, writes always require human approval. Use both regex AND LLM double-checking to classify SQL before execution.
- Data masking required on sensitive fields (phone numbers, ID numbers) before returning results.
- Per-user concurrency rate limiting via FastAPI to prevent LLM resource exhaustion.
- Target: simple queries < 5s end-to-end, complex queries < 15s, first-byte SSE < 1s.
- New database dialects are added via config + SQL dialect template (`app/db/dialects/`) — core Agent logic must not change.
- Redis checkpoint TTL is 1 hour (`checkpointer.py:CHECKPOINT_TTL`) — approval-awaiting tasks expire after this.

## SSE Event Types (前端 Backend 协议)

后端通过 SSE 流式推送以下事件类型到前端 `useSSE.ts` composable：

| event.type | callback | 用途 |
|-----------|----------|------|
| `status` | onStatus | 流程状态更新（如"正在分析 schema..."） |
| `schema` | onSchema | Schema Agent 加载的表结构信息 |
| `sql` | onSQL | SQL Coder 生成的 SQL 语句 |
| `text` | onText | 自然语言文本（分析/回答） |
| `result` | onResult | 查询结果数据 + 列名 |
| `error` | onError | 错误信息 |
| `done` | onDone | 流正常结束 |
| `approval_required` | onApprovalRequired | 高危 SQL 需要审批（thread_id, question, sql, reason） |

- 当你在提示词中包含 use context7 时，服务器会获取当前官方文档和代码示例，并直接集成到你的 AI 助手的上下文窗口中