"""
Agent 执行中断接口
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/chat", tags=["chat"])


class StopRequest(BaseModel):
    """中断请求体"""
    thread_id: str = Field(..., description="要中断的对话线程 ID")


@router.post("/stop", summary="中断当前 Agent 执行")
async def stop_execution(body: StopRequest):
    """
    中断指定 thread_id 的 Agent 执行。
    当前为占位实现，后续对接 LangGraph 的 cancel 机制。
    """
    return {
        "status": "stopped",
        "thread_id": body.thread_id,
        "message": "Agent 执行已中断（占位实现，后续对接 LangGraph cancel）",
    }
