# 架构设计

本文档详细阐述 DataAgent Pro 的整体分层架构、多智能体协作模式及技术选型理由。

## 整体分层架构

系统采用 **六层架构**，自顶向下分别为：

```
┌──────────────────────────────────────────────┐
│  表现层     Vue 3 + Element Plus + ECharts    │  用户界面
├──────────────────────────────────────────────┤
│  网关层     FastAPI (REST + SSE Streaming)    │  请求路由
├──────────────────────────────────────────────┤
│  编排层     LangGraph 1.x StateGraph          │  工作流引擎
├──────────────────────────────────────────────┤
│  智能体层   7 个专职 Agent (Hermes 模式)       │  业务逻辑
├──────────────────────────────────────────────┤
│  基座层     LLM Client / RAG / DB Connector   │  基础设施
├──────────────────────────────────────────────┤
│  存储层     MySQL / PG / Milvus / Redis       │  数据持久化
└──────────────────────────────────────────────┘
```

### 表现层

- 基于 **Vue 3** Composition API + **Vite** 构建
- UI 组件库：**Element Plus**
- 可视化：**ECharts**（图表渲染）+ **ECharts JSON** 动态配置
- 状态管理：**Pinia**
- 流式通信：**EventSource (SSE)** 接收后端流式响应

### 网关层

- **FastAPI** 异步框架，提供 REST 接口和 SSE 流式端点
- 核心路由：
  - `POST /api/v1/chat/completions` — 对话入口（SSE 流式返回）
  - `POST /api/v1/chat/approve` — 管理员审批回调
  - `POST /api/v1/chat/stop` — 中断 Agent 执行
  - `GET /api/v1/datasource/list` — 数据源列表
  - `POST /api/v1/export/excel` — 文件导出

### 编排层

- **LangGraph 1.x StateGraph** 作为工作流引擎
- 全局状态对象 `AgentState` 在节点间流转
- 支持 **Human-in-the-loop** 中断/恢复（基于 Redis 快照）
- 条件边实现动态路由和错误短路

### 智能体层

详见 [Hermes 多智能体模式](#hermes-多智能体模式)。

### 基座层

- **LLM Client**：封装 Qwen/GLM 大模型调用，支持统一接口切换
- **RAG Engine**：文档切片 → Embedding → Milvus 向量检索
- **DB Connector**：SQLAlchemy 多方言会话管理

### 存储层

- **业务数据库**：MySQL / PostgreSQL / SQL Server / Oracle（用户真实数据）
- **向量数据库**：Milvus 2.x（知识库文档索引）
- **缓存/状态**：Redis（Graph 中断状态快照 + 限流计数）

---

## Hermes 多智能体模式

DataAgent Pro 采用 **控制平面 + 数据平面 + 专家 Worker** 的 Hermes 架构：

```
┌──────────────────────────────────────────┐
│          控制平面 (Control Plane)          │
│  ┌────────────────────────────────────┐  │
│  │    Orchestrator Agent              │  │
│  │  · 意图解析                         │  │
│  │  · 任务拆解                         │  │
│  │  · Graph 状态管理                   │  │
│  │  · 动态路由                         │  │
│  └──────────┬─────────────────────────┘  │
└─────────────┼────────────────────────────┘
              │ 调度
    ┌─────────┼─────────┬─────────┬─────────┐
    ▼         ▼         ▼         ▼         ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│ RAG   │ │Schema │ │SQL    │ │Security│ │Analyst│
│ Agent │ │Agent  │ │Coder  │ │Agent   │ │Agent  │
└───────┘ └───────┘ └───────┘ └───────┘ └───────┘
                                         ┌───────┐
                                         │Reporter│
                                         │Agent   │
                                         └───────┘
            数据平面 — 专家 Worker
```

### 7 个 Agent 的职责与协作

| # | Agent | 职责 | 输入 | 输出 |
|---|-------|------|------|------|
| 1 | **Orchestrator** | 意图解析、任务拆解、路由决策 | 用户自然语言 | 任务计划、调用指令 |
| 2 | **RAG Agent** | 从知识库检索业务规范、指标定义 | 用户问题 | 相关文档片段 |
| 3 | **Schema Agent** | 动态加载相关表结构，过滤无关表 | 表名列表 | 精简的 DDL 信息 |
| 4 | **SQL Coder** | 生成方言特定的 SQL，执行失败自动重试（最多 2 次） | Schema + 需求 | 可执行 SQL |
| 5 | **Security Agent** | SQL 审计分类（读/写），数据脱敏 | SQL 文本 | 安全标记 + 脱敏后的结果 |
| 6 | **Analyst Agent** | 统计分析（同比、环比、异常检测） | 查询结果 | 自然语言洞察 |
| 7 | **Reporter Agent** | 图表推荐 + ECharts JSON 生成，或 Excel 导出 | 分析结果 | 可视化配置 / 文件 |

---

## LangGraph 工作流拓扑

```
                      ┌──────────┐
                      │  START   │
                      └────┬─────┘
                           ▼
                   ┌───────────────┐
                   │ Orchestrator  │
                   └───────┬───────┘
                           ▼
                   ┌───────────────┐
                   │   RAG Agent   │
                   └───────┬───────┘
                           ▼
                   ┌───────────────┐
                   │ Schema Agent  │
                   └───────┬───────┘
                           ▼
                   ┌───────────────┐
                   │  SQL Coder    │
                   └───────┬───────┘
                           ▼
                   ┌───────────────┐
                   │Security Agent │
                   └───┬───────┬───┘
              SELECT    │       │  INSERT/UPDATE/DELETE/DROP
                        ▼       ▼
                ┌──────────┐  ┌──────────────┐
                │Execute   │  │ Graph Interrupt│
                │SQL Node  │  │ (等待审批)     │
                └────┬─────┘  └──────┬───────┘
                     ▼               ▼
              ┌──────────┐   ┌──────────────┐
              │ Analyst  │   │ /approve 回调  │
              │ Agent    │   └──────┬───────┘
              └────┬─────┘          ▼
                   ▼          ┌──────────────┐
              ┌──────────┐   │ 审批通过 →     │
              │ Reporter │   │ 执行 SQL       │
              │ Agent    │   │ 审批拒绝 →     │
              └────┬─────┘   │ 返回拒绝信息    │
                   ▼         └──────────────┘
              ┌──────────┐
              │   END    │
              └──────────┘
```

---

## 技术选型说明

### 为什么选择 FastAPI

- 原生异步支持，完美适配 LLM 调用的 I/O 密集场景
- 内置 SSE 支持（`StreamingResponse`），无需额外中间件
- 自动生成 OpenAPI 文档，降低前后端联调成本
- Pydantic 类型校验，减少运行时错误

### 为什么选择 LangGraph 1.x

- 有状态工作流：`AgentState` 贯穿全流程，便于追踪和调试
- 原生 Human-in-the-loop：`interrupt()` + `Command(resume=...)` 机制
- 条件边支持：可根据运行时状态动态路由
- 状态持久化：集成 Redis Checkpointer，服务重启不丢失中断状态

### 为什么选择 SQLAlchemy

- 统一的多方言 API：同一套代码适配 MySQL、PostgreSQL、SQL Server、Oracle
- ORM 与原生 SQL 混合使用，灵活应对复杂查询
- 连接池管理，保障高并发下的数据库连接稳定性

### 为什么选择 Milvus

- 专为向量检索设计的分布式架构，10 亿级数据毫秒级响应
- 支持多种索引类型（IVF_FLAT、HNSW），可根据场景调优
- 与 LangChain 生态无缝集成
