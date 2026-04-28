# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hermes Text-to-SQL AI Agent: A natural language to SQL conversion assistant with analysis, visualization, and safety controls. The system uses LangGraph for state-driven agent orchestration, supporting multi-database queries with RAG-powered operation guides and human approval workflows for sensitive operations.

## Architecture

**Five-layer architecture:**

1. **Interactive Layer**: Vue 3 + Element Plus chat interface + FastAPI endpoints
2. **Agent Core Layer**: LangGraph state machine with intent routing, dialogue memory, security approval engine
3. **Tools & Skills Layer**: SQL generation/validation, data analysis, RAG operation specs, third-party agent integration
4. **Data & Knowledge Layer**: SQLAlchemy multi-dialect connections (MySQL, PostgreSQL, Oracle, SQL Server) + Milvus vector database
5. **Infrastructure Layer**: Docker + Docker Compose deployment

## Technology Stack

- **Agent Framework**: LangChain + LangGraph (state-driven orchestration)
- **LLM**: OpenAI-compatible models (GPT-4o, DeepSeek, Qwen) - pluggable via model provider abstraction
- **Backend**: Python 3.11+, FastAPI (async)
- **Frontend**: Vue 3 + Vite + Element Plus
- **Database ORM**: SQLAlchemy with multi-dialect support
- **Vector DB**: Milvus (pymilvus) for embeddings
- **Embedding Models**: text-embedding-3-large or bge-m3
- **Visualization**: ECharts (frontend), matplotlib (backend export)
- **Documentation**: VitePress

## Core Workflows

**Text-to-SQL flow:**
```
User Input → Intent Classification → RAG Retrieval (if needed)
    → SQL Generation → SQL Validation → (SELECT) Execution
    → Result Analysis → Natural Language Summary → Visualization/Report
```

**Sensitive operation flow:**
```
Non-SELECT /高危表/DML → SQL Generation → Approval Request → Human Review
    → Approved → Execute + Audit Log
    → Rejected → Notify User
```

## Project Structure (Planned)

```
hermes-tts-agent/
├── backend/           # FastAPI application
│   ├── agents/        # LangGraph agent definitions
│   ├── tools/         # SQL generation, validation, analysis
│   ├── skills/        # RAG, approval, visualization
│   ├── models/        # Database schemas
│   └── main.py        # FastAPI entry point
├── frontend/          # Vue 3 application
├── docker/            # Docker configurations
├── docs/              # VitePress documentation
└── scripts/           # Initialization, embedding generation
```

## Key Components

**Agent State Machine (LangGraph):**
- Node types: `router`, `rag_retriever`, `sql_generator`, `sql_validator`, `executor`, `approver`, `analyzer`
- State: `conversation_history`, `current_query`, `sql_generated`, `validation_result`, `approval_status`

**RAG System:**
- Vector store: Milvus with table schema embeddings
- Knowledge types: Database dictionary, SQL writing standards, business operation manuals, historical queries
- Retrieval: Top-K similarity search before SQL generation

**Security/Approval:**
- Operations requiring approval: INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE on high-risk tables
- Approval workflow: Agent creates request → Frontend/API review → Approval/Rejection with notes
- Audit logging: All operations stored with user, timestamp, SQL, result

**Multi-Database Support:**
- SQLAlchemy engine creation per database type
- Dynamic schema reading via SQLAlchemy metadata
- SQL dialect adaptation (MySQL vs PostgreSQL syntax)

## Deployment

- **Single-command**: `docker-compose up --build`
- **Components**: backend, frontend, milvus, nginx
- **Environment**: Copy `.env.example` to `.env` and configure database connections, LLM API keys

## Development Commands (Post-Initial Setup)

- Backend: `cd backend && uvicorn main:app --reload`
- Frontend: `cd frontend && npm run dev`
- Tests: (to be defined)
- Lint: (to be defined)
