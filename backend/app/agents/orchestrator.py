"""
Orchestrator Agent - 控制枢纽
接收用户意图，进行任务拆解与路由判断
负责将用户请求分发到合适的下游 Agent（Schema Agent / RAG Agent）
"""
import json

from app.core.config import settings
from app.core.llm import get_llm


async def analyze_intent(user_question: str) -> dict:
    """
    调用 LLM 分析用户意图，分类为查询数据、询问帮助或写入数据。

    参数:
        user_question: 用户输入的自然语言问题

    返回:
        {
            "intent": "query_data" | "ask_help" | "write_data",
            "confidence": float  # 置信度，范围 0.0 ~ 1.0
        }

        若 LLM 返回解析失败，默认返回 query_data 兜底。
    """
    client = get_llm()

    system_prompt = (
        "你是一个智能路由分析专家。"
        "请分析用户的问题，判断其意图属于以下哪一类：\n\n"
        "1. query_data —— 用户想要查询、检索或统计数据（生成 SQL 查询）\n"
        "   示例: \"上个月销量最高的产品是什么？\" \"有多少注册用户？\"\n\n"
        "2. ask_help —— 用户询问系统使用方法、功能说明或概念性问题（走 RAG 知识库）\n"
        "   示例: \"怎么导出报表？\" \"这个系统支持哪些数据库？\" \"什么是索引？\"\n\n"
        "3. write_data —— 用户想要插入、更新、删除数据或修改表结构（需要审批流）\n"
        "   示例: \"把所有北京用户的等级改成 VIP\" \"删除无效订单\"\n\n"
        "严格要求：\n"
        "1. 只返回一个 JSON 对象，不要包含任何其他文字\n"
        "2. JSON 格式为: {\"intent\": \"<类型>\", \"confidence\": <0.0~1.0>}\n"
        "3. 不要使用 markdown 代码块包裹 JSON"
    )

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请分析以下用户意图：\n\n{user_question}"},
            ],
            temperature=0.0,
        )

        content = response.choices[0].message.content.strip()
        # 尝试从 markdown 代码块中提取 JSON
        if content.startswith("```"):
            content = _extract_json_from_markdown(content)

        result = json.loads(content)

        # 校验返回字段的合法性
        valid_intents = {"query_data", "ask_help", "write_data"}
        intent = result.get("intent", "query_data")
        confidence = float(result.get("confidence", 0.5))

        if intent not in valid_intents:
            intent = "query_data"  # 非法值兜底

        # 将 confidence 钳制在 0.0 ~ 1.0 范围
        confidence = max(0.0, min(1.0, confidence))

        return {"intent": intent, "confidence": confidence}

    except (json.JSONDecodeError, Exception):
        # LLM 返回解析失败，默认按查询数据处理
        return {"intent": "query_data", "confidence": 0.5}


def _extract_json_from_markdown(text: str) -> str:
    """
    从 markdown 代码块中提取 JSON 内容。

    参数:
        text: 可能包含 markdown 标记的文本

    返回:
        提取后的纯 JSON 字符串
    """
    lines = text.split("\n")
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


async def route_by_intent(intent_result: dict) -> str:
    """
    根据意图分析结果，返回下一步应调用的 Agent 节点名称。

    路由规则：
    - query_data  → schema_agent（查数据，走 Schema → SQL → 执行链路）
    - ask_help    → rag_agent（咨询类问题，走 RAG 知识库检索）
    - write_data  → schema_agent（写入数据，也走 Schema → SQL → Security 链路）
    - 未知意图    → schema_agent（默认尝试走查询链路）

    参数:
        intent_result: analyze_intent() 的返回结果，
                       包含 "intent" 和 "confidence" 字段

    返回:
        下游 Agent 节点名称字符串
    """
    intent = intent_result.get("intent", "query_data")

    # 路由映射表
    route_map = {
        "query_data": "schema_agent",
        "ask_help": "rag_agent",
        "write_data": "schema_agent",  # 也走 Schema → SQL → Security 链路
    }

    return route_map.get(intent, "schema_agent")
