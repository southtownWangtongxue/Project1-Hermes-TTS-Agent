from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, List
from sqlalchemy.orm import Session
import sys
from .config import settings
from .utils import logger
from .models.database import init_db, get_db
from .models.schemas import SessionSchema
from .agents.state import AgentState
from .agents.router import route_intent, route_sensitive_operation

# 常量定义
APP_NAME = "Hermes Text-to-SQL Agent"
APP_VERSION = "0.1.0"
APP_STATUS = "running"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    try:
        logger.info(f"Starting {APP_NAME} backend v{APP_VERSION}...")
        init_db()
        yield
        logger.info(f"Shutting down {APP_NAME} backend...")
    except Exception as e:
        logger.error(f"Error during application lifecycle: {e}", exc_info=True)

def check_dependencies() -> Dict[str, bool]:
    """检查必需的依赖包"""
    dependencies = {
        "fastapi": False,
        "uvicorn": False,
        "sqlalchemy": False,
        "pydantic": False,
    }

    for package in dependencies.keys():
        try:
            __import__(package)
            dependencies[package] = True
        except ImportError:
            dependencies[package] = False

    return dependencies

# 检查依赖
missing_deps = [pkg for pkg, available in check_dependencies().items() if not available]
if missing_deps:
    print("Warning: Missing required dependencies:", ", ".join(missing_deps), file=sys.stderr)
    print("Install with: pip install -r requirements.txt", file=sys.stderr)

app = FastAPI(
    title=APP_NAME,
    description="Natural language to SQL conversion assistant",
    version=APP_VERSION,
    lifespan=lifespan
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应配置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 定义 LangGraph 图结构（阶段1先定义，具体节点稍后实现）
# from langgraph.graph import StateGraph
# workflow = StateGraph(AgentState)
# workflow.add_node("router", route_intent)
# workflow.add_node("query_processor", query_processor_node)
# workflow.add_node("approver", approver_node)
# workflow.set_entry_point("router")
# workflow.add_conditional_edges("router", route_sensitive_operation, {
#     "approver": "approver",
#     "query": "query_processor"
# })
# workflow.add_edge("query_processor", "approver")
# workflow.add_edge("approver", "query_processor")
# app_state = workflow.compile()

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": APP_STATUS
    }

@app.get("/health")
async def health():
    """健康检查端点"""
    return {"status": "healthy"}

@app.get("/api/v1/sessions")
async def list_sessions(db: Session = Depends(get_db)):
    """
    获取所有会话列表

    Args:
        db: 数据库会话（通过依赖注入自动管理）

    Returns:
        dict: 包含会话列表的响应
    """
    try:
        sessions = db.query(Session).all()
        return {"sessions": [s.dict() for s in sessions]}
    except Exception as e:
        logger.error(f"Error fetching sessions: {e}", exc_info=True)
        raise e

if __name__ == "__main__":
    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host=settings.FASTAPI_HOST,
            port=settings.FASTAPI_PORT,
            reload=True
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)
