from fastapi import FastAPI
from contextlib import asynccontextmanager
from .config import settings
from .utils import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Starting Hermes TTS Agent backend...")
    yield
    logger.info("Shutting down Hermes TTS Agent backend...")

app = FastAPI(
    title="Hermes Text-to-SQL Agent",
    description="Natural language to SQL conversion assistant",
    version="0.1.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {
        "name": "Hermes Text-to-SQL Agent",
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.FASTAPI_HOST,
        port=settings.FASTAPI_PORT,
        reload=True
    )
