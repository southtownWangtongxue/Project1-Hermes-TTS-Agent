from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict
import sys
from .config import settings
from .utils import logger
from .models.database import init_db

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
async def list_sessions():
    from .models.database import SessionLocal, SessionCreate
    from .models.schemas import Session
    from datetime import datetime

    db = SessionLocal()
    try:
        sessions = []
        # 这里应该从数据库查询会话列表
        # 目前返回空列表
        return {"sessions": sessions}
    finally:
        db.close()

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
