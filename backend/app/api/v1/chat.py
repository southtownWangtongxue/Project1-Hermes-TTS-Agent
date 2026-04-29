"""
聊天接口 —— SSE 流式对话

提供基于 Server-Sent Events 的流式对话能力。
后端通过 LangGraph 的 astream() 方法监听各 Agent 节点的
状态变更，将关键信息实时推送给前端（状态、SQL、结果、
分析洞察、图表配置等）。
"""
import json
import logging
import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.graph.workflow import get_graph

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


# ================================================================
# 数据模型
# ================================================================


class ChatMessage(BaseModel):
    """单条对话消息"""
    role: str = Field(..., description="消息角色: user / assistant / system")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    """聊天请求体"""
    messages: list[ChatMessage] = Field(
        default_factory=list,
        description="对话历史消息列表",
    )
    stream: bool = Field(
        default=True,
        description="是否启用 SSE 流式响应",
    )


# ================================================================
# 内部辅助函数
# ================================================================


def _sse_event(data: dict) -> str:
    """
    构造 SSE 事件字符串（符合 Server-Sent Events 规范）。

    参数:
        data: 事件数据字典，将被 JSON 序列化

    返回:
        形如 "data: {...}\n\n" 的 SSE 事件字符串
    """
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


# ================================================================
# SSE 流式对话生成器
# ================================================================


async def _stream_chat(question: str):
    """
    SSE 流式对话生成器 —— 异步生成 SSE 事件流。

    执行流程：
        1. 创建 LangGraph 执行上下文（含 thread_id，用于审批恢复）
        2. 通过 graph.astream() 监听各节点状态变更
        3. 根据节点名称分发对应的 SSE 事件（status / sql / result /
           analysis / chart / error / done）

    参数:
        question: 用户最新输入的自然语言问题

    产出:
        SSE 事件字符串，每个事件一行 "data: {...}\n\n"
    """
    graph = get_graph()

    # 构造初始状态
    initial_state = {
        "user_question": question,
        "messages": [],
    }

    # 生成唯一 thread_id，用于 Human-in-the-loop 审批恢复
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    try:
        # 使用 astream 流式监听各节点产出（stream_mode="updates"）
        async for event in graph.astream(
            initial_state, config, stream_mode="updates"
        ):
            for node_name, state_update in event.items():
                # ── orchestrator: 意图分析与路由 ──────────
                if node_name == "orchestrator":
                    logger.info("[SSE] orchestrator 阶段完成")
                    yield _sse_event({
                        "type": "status",
                        "content": "正在分析您的意图...",
                    })

                # ── schema_agent: 加载表结构 ──────────────
                elif node_name == "schema_agent":
                    logger.info("[SSE] schema_agent 阶段完成")
                    yield _sse_event({
                        "type": "status",
                        "content": "正在加载数据表结构...",
                    })

                # ── sql_coder: SQL 生成 ──────────────────
                elif node_name == "sql_coder":
                    sql = state_update.get("generated_sql", "")
                    if sql:
                        logger.info("[SSE] 推送 SQL: %s", sql[:80])
                        yield _sse_event({
                            "type": "sql",
                            "content": sql,
                        })

                # ── security: SQL 安全审核 ───────────────
                elif node_name == "security":
                    logger.info("[SSE] security 阶段完成")
                    yield _sse_event({
                        "type": "status",
                        "content": "正在审核 SQL 安全性...",
                    })

                # ── execute_sql: SQL 执行 ────────────────
                elif node_name == "execute_sql":
                    # 推送查询结果
                    results = state_update.get("query_result", [])
                    columns = state_update.get("query_columns", [])
                    if results:
                        logger.info(
                            "[SSE] 推送查询结果: %d 行 %d 列",
                            len(results),
                            len(columns),
                        )
                        yield _sse_event({
                            "type": "result",
                            "data": results,
                            "columns": columns,
                        })

                    # 推送执行错误（如有）
                    error = state_update.get("error_message", "")
                    if error:
                        logger.warning("[SSE] SQL 执行异常: %s", error)
                        yield _sse_event({
                            "type": "error",
                            "error": error,
                        })

                # ── analyst: 数据分析 ────────────────────
                elif node_name == "analyst":
                    yield _sse_event({
                        "type": "status",
                        "content": "数据分析完成",
                    })
                    analysis_text = state_update.get("analysis_text", "")
                    if analysis_text:
                        logger.info(
                            "[SSE] 推送分析结果: %s",
                            analysis_text[:80],
                        )
                        yield _sse_event({
                            "type": "analysis",
                            "content": analysis_text,
                        })

                # ── reporter: 图表生成 ────────────────────
                elif node_name == "reporter":
                    yield _sse_event({
                        "type": "status",
                        "content": "图表生成完成",
                    })
                    chart_config = state_update.get("chart_config")
                    if chart_config:
                        logger.info(
                            "[SSE] 推送图表配置: type=%s",
                            chart_config.get("chart_type", "unknown"),
                        )
                        yield _sse_event({
                            "type": "chart",
                            "config": chart_config,
                        })

                # ── rag_agent: RAG 知识库检索 ────────────
                elif node_name == "rag_agent":
                    text = state_update.get("analysis_text", "")
                    if text:
                        logger.info("[SSE] RAG 检索结果: %s", text[:80])
                        yield _sse_event({
                            "type": "status",
                            "content": text,
                        })

                # ── finish: 工作流结束 ────────────────────
                elif node_name == "finish":
                    logger.info("[SSE] 工作流执行完毕")
                    yield _sse_event({"type": "done"})

    except Exception as exc:
        logger.exception("[SSE] 流式对话异常")
        yield _sse_event({
            "type": "error",
            "error": f"处理异常: {str(exc)}",
        })


# ================================================================
# API 路由
# ================================================================


@router.post("/completions", summary="SSE 流式对话")
async def chat_completions(body: ChatRequest):
    """
    SSE 流式对话接口 —— 接收用户问题，返回 Server-Sent Events 流。

    请求体：
        - messages: 对话历史（取最后一条作为当前用户问题）
        - stream: 是否启用流式响应（默认 true）

    响应：
        text/event-stream 格式的 SSE 事件流，包含以下事件类型：
        - status: 流程状态推送（如"正在分析..."）
        - sql: 生成的 SQL 语句
        - result: SQL 执行结果（data + columns）
        - analysis: 数据分析洞察
        - chart: ECharts 图表配置
        - error: 错误信息
        - done: 流程结束
    """
    # 从请求中提取用户最新问题
    question = body.messages[-1].content if body.messages else ""

    return StreamingResponse(
        _stream_chat(question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
