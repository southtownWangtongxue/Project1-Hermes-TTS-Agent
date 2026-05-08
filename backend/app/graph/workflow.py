"""
LangGraph 工作流定义
基于 Hermes 架构的 Multi-Agent 状态图

完整处理链路：
    orchestrator ──┬── schema_agent → sql_coder → security ──┬── execute_sql → analyst → reporter → finish
                   │                               (高危拦截)  │
                   └── rag_agent ─────────────────────────────┘

Security 节点内置 Human-in-the-loop 审批中断机制：
    当 SQL 被 Security Agent (classify_sql) 判定为高危操作时，
    通过 langgraph.types.interrupt() 挂起 Graph 执行，等待外部
    通过 Command(resume=...) 传入审批结果后恢复执行。

节点职责：
    orchestrator  - 调用 Orchestrator Agent 分析用户意图并路由
    schema_agent  - 加载数据库表结构，筛选相关表
    sql_coder     - 调用 LLM 根据表结构生成目标 SQL
    security      - 调用 Security Agent 审核 SQL，高危操作触发审批中断
    execute_sql   - 在业务数据库上执行已通过审核的 SQL
    analyst       - 调用 Analyst Agent 对查询结果进行统计分析
    reporter      - 调用 Reporter Agent 生成 ECharts 图表配置
    rag_agent     - RAG 知识库检索（帮助咨询类问题，当前占位）
    finish        - 结束节点，标记工作流执行完毕
"""
import logging

from langgraph.graph import StateGraph, END
from langgraph.types import interrupt, Command

from app.agents.misc_agent import misc_agent
from app.agents.orchestrator import analyze_intent, route_by_intent
from app.agents.schema_agent import get_table_schemas, filter_relevant_tables
from app.agents.sql_coder import generate_sql, execute_sql
from app.agents.security import classify_sql
from app.agents.analyst import analyze_results
from app.agents.reporter import generate_chart_config
from app.db.session import get_engine
from app.graph.state import AgentState

logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
# ================================================================
# 节点函数
# ================================================================


async def orchestrator_node(state: AgentState) -> dict:
    """
    编排节点 —— 调用 Orchestrator Agent 分析用户意图，确定下游路由。

    通过 LLM 将用户问题分类为三类意图之一：
        - query_data:  数据查询（走 Schema → SQL → Execute 链路）
        - ask_help:    帮助咨询（走 RAG 知识库检索链路）
        - write_data:  数据写入（走 SQL 链路，后续由 Security 拦截审批）

    参数:
        state: 当前 Agent 全局状态，需包含 user_question

    返回:
        包含 intent、intent_confidence 和 stage 的部分状态更新
    """
    user_question = state.get("user_question", "")

    if not user_question.strip():
        logger.warning("[Orchestrator] 用户问题为空")
        return {
            "intent": "query_data",
            "intent_confidence": 0.0,
            "error_message": "用户问题为空",
            "stage": "orchestrated",
        }

    # 调用 Orchestrator Agent 进行意图分析
    logger.info("[Orchestrator] 分析用户意图: %s", user_question[:80])
    result = await analyze_intent(user_question)

    logger.info(
        "[Orchestrator] 意图分析完成: intent=%s, confidence=%.2f",
        result["intent"],
        result["confidence"],
    )

    return {
        "intent": result["intent"],
        "intent_confidence": result["confidence"],
        "stage": "orchestrated",
    }
async def misc_node(state: AgentState) -> dict:
    """
    杂项节点 —— 调用 misc Agent 回答用户。
    参数:
        state: 当前 Agent 全局状态，需包含 user_question

    返回:
        包含   stage 的部分状态更新
    """
    user_question = state.get("user_question", "")

    if not user_question.strip():
        logger.warning("[misc_node] 用户问题为空")
        return {

            "error_message": "用户问题为空",
            "stage": "misc",
        }

    # 调用 Misc Agent
    logger.info("[Misc] 调用 misc Agent: %s", user_question[:80])
    result = await misc_agent(user_question)

    logger.info(
        "[misc_node] 调用 misc Agent完成: intent=%s",
        result
    )
    msg=state.get("messages", "")
    logger.info(msg)
    return {
        'messages': [result],
        "stage": "misc",
    }


def route_orchestrator(state: AgentState) -> str:
    """
    编排路由 —— 根据意图分析结果决定下一节点。

    使用 Orchestrator 内置的 route_by_intent() 进行路由映射：
        - query_data  → schema_agent（数据查询，走 SQL 生成与执行链路）
        - ask_help    → rag_agent（帮助咨询，走 RAG 知识库检索）
        - write_data  → schema_agent（数据写入，走 SQL 链路，由 Security 拦截审批）
        - other_questions  →misc_agent 其他类型
        - 未知意图    → schema_agent（默认走查询链路兜底）

    参数:
        state: 当前 Agent 全局状态（已包含 orchestrator_node 写入的 intent 字段）

    返回:
        下游节点名称: "schema_agent" 或 "rag_agent"
    """
    # 从状态中提取意图分析结果，构建 route_by_intent 所需的参数
    intent_result = {
        "intent": state.get("intent", "query_data"),
        "confidence": state.get("intent_confidence", 0.5),
    }

    route =  route_by_intent(intent_result)
    logger.info("[Orchestrator] 路由决策: %s → %s", intent_result["intent"], route)
    return route


async def schema_node(state: AgentState) -> dict:
    """
    Schema Agent 节点 —— 连接业务数据库，加载表结构并筛选相关表。

    处理步骤：
        1. 获取数据库中所有表的完整结构信息
        2. 根据用户问题中的关键词匹配，筛选出相关表
        3. 若筛选成功则仅保留相关表结构，降低后续 LLM 调用的 Token 消耗
        4. 若筛选失败则保留全部表结构作为兜底

    参数:
        state: 当前 Agent 全局状态，需包含 user_question

    返回:
        包含 schema_info、relevant_tables 和 stage 的部分状态更新；
        数据库连接失败时设置 error_message
    """
    user_question = state.get("user_question", "")

    try:
        engine = get_engine()

        # 第一步：获取所有表结构
        schema_text = await get_table_schemas(engine)

        # 第二步：根据用户问题筛选相关表，降低 Token 消耗
        relevant_tables = await filter_relevant_tables(engine, user_question)
        if relevant_tables:
            schema_text = await get_table_schemas(engine, relevant_tables)

        logger.info(
            "[SchemaAgent] 表结构加载完成，相关表: %s",
            relevant_tables if relevant_tables else "全部",
        )

        return {
            "schema_info": schema_text,
            "relevant_tables": relevant_tables,
            "stage": "schema_loaded",
        }
    except Exception as exc:
        logger.exception("[SchemaAgent] 表结构加载失败")
        return {
            "error_message": f"加载表结构失败: {str(exc)}",
            "stage": "schema_loaded",
        }


async def sql_coder_node(state: AgentState) -> dict:
    """
    SQL Coder 节点 —— 调用 LLM 将自然语言问题与表结构转换为目标 SQL。

    关键约束：
        - 仅生成 SQL，不在此节点执行
        - SQL 执行将在 Security 节点审核通过之后，由 execute_sql 节点完成
        - 如需自校正（生成失败时重试），请在后续迭代中集成
          sql_coder.generate_and_execute_sql

    参数:
        state: 当前 Agent 全局状态，需包含 user_question 和 schema_info

    返回:
        包含 generated_sql 和 stage 的部分状态更新；
        schema_info 为空或 LLM 调用失败时设置 error_message
    """
    user_question = state.get("user_question", "")
    schema_info = state.get("schema_info", "")

    if not schema_info:
        logger.warning("[SQLCoder] 表结构信息为空，无法生成 SQL")
        return {
            "error_message": "表结构信息为空，无法生成 SQL",
            "stage": "sql_generated",
        }

    try:
        sql = await generate_sql(
            user_question=user_question,
            schema_info=schema_info,
        )
        logger.info("[SQLCoder] SQL 生成完成: %s", sql[:120])
        return {
            "generated_sql": sql,
            "stage": "sql_generated",
        }
    except Exception as exc:
        logger.exception("[SQLCoder] SQL 生成失败")
        return {
            "error_message": f"SQL 生成失败: {str(exc)}",
            "stage": "sql_generated",
        }


async def security_node(state: AgentState) -> dict:
    """
    Security 节点 —— 调用 Security Agent 审核生成的 SQL，高危操作触发审批中断。

    审核流程：
        1. 调用 security.classify_sql() 对 SQL 进行安全分类
           （采用正则 + LLM 双检策略，返回 category: "safe" 或 "dangerous"）
        2. 若为 "dangerous" 高危操作：
           a. 调用 interrupt() 挂起 Graph 执行，等待外部审批
           b. Graph 恢复时，interrupt() 返回 Command(resume=...) 传入的审批结果
           c. 审批通过 → sql_category 设为 "safe" 放行
           d. 审批驳回 → 设置 error_message，后续由 route_security 路由至 finish
        3. 若为 "safe" 安全操作：直接放行

    Human-in-the-loop 说明：
        当 interrupt() 被调用时，LangGraph 保存当前检查点并挂起执行。
        外部系统通过以下方式恢复：
            from langgraph.types import Command
            graph.invoke(Command(resume={"approved": True}), config)

        由于 LangGraph 在中断恢复后会完全重新执行节点函数，
        classify_sql() 会被调用两次（首次执行和恢复时各一次）。
        classify_sql 通过正则优先匹配保证确定性，LLM 二次确认开销可控。

    参数:
        state: 当前 Agent 全局状态，需包含 generated_sql

    返回:
        包含 sql_category、stage 的部分状态更新；
        审批驳回时额外设置 error_message
    """
    sql = state.get("generated_sql", "")

    if not sql:
        logger.warning("[Security] SQL 为空，跳过安全检查")
        return {
            "sql_category": "safe",
            "error_message": "SQL 生成结果为空，跳过安全检查",
            "stage": "security_checked",
        }

    # 调用 Security Agent 进行安全分类（正则 + LLM 双检）
    logger.info("[Security] 审核 SQL: %s", sql[:120])
    result = await classify_sql(sql)
    category = result["category"]

    logger.info(
        "[Security] 分类结果: category=%s, method=%s, reason=%s",
        category,
        result["method"],
        result["reason"],
    )

    if category == "dangerous":
        # ── Human-in-the-loop 审批中断 ──
        # 首次执行: interrupt() 抛出 GraphInterrupt，Graph 挂起
        # 恢复执行: interrupt() 返回 Command(resume=...) 传入的审批结果
        logger.warning("[Security] 检测到高危 SQL，等待人工审批")

        approval = interrupt({
            "type": "approval_required",
            "message": "检测到高危 SQL 操作（非只读），需要管理员审批",
            "sql": sql,
            "reason": result.get("reason", ""),
        })

        # approval 格式: {"approved": True/False, "comment": "审批备注"}
        if approval.get("approved"):
            logger.info("[Security] 审批通过，放行执行")
            return {
                "sql_category": "safe",
                "stage": "security_checked",
            }
        else:
            logger.info(
                "[Security] 审批被驳回: %s",
                approval.get("comment", "无备注"),
            )
            return {
                "sql_category": category,
                "error_message": f"审批被驳回: {approval.get('comment', '无备注')}",
                "stage": "security_checked",
            }

    # 安全操作：直接放行
    logger.info("[Security] SQL 安全检查通过（只读操作）")
    return {
        "sql_category": category,
        "stage": "security_checked",
    }


def route_security(state: AgentState) -> str:
    """
    Security 路由 —— 根据安全审查结果决定下一节点。

    路由规则（优先级从高到低）：
        1. error_message 中包含 "驳回" → "finish"（审批被拒绝，终止执行）
        2. sql_category == "safe" → "execute_sql"（安全操作或审批通过，执行 SQL）
        3. 其他情况 → "finish"（兜底终止）

    参数:
        state: 当前 Agent 全局状态，需包含 sql_category 和 error_message

    返回:
        下游节点名称: "execute_sql" 或 "finish"
    """
    sql_category = state.get("sql_category", "")
    error_message = state.get("error_message", "")

    # 审批被驳回：终止流程
    if error_message and "驳回" in error_message:
        logger.info("[Security] 路由: 审批被驳回 → finish")
        return "finish"

    # 安全操作或审批通过：进入执行
    if sql_category == "safe":
        logger.info("[Security] 路由: 安全/审批通过 → execute_sql")
        return "execute_sql"

    # 兜底：未知状态，终止流程
    logger.warning(
        "[Security] 路由: 未知状态 (category=%s) → finish",
        sql_category,
    )
    return "finish"


async def execute_node(state: AgentState) -> dict:
    """
    SQL 执行节点 —— 在业务数据库上执行已通过安全审核的 SQL。

    设计说明：
        仅调用 execute_sql() 执行单次 SQL，不启用自动重试。
        SQL 生成的正确性由上游 sql_coder_node 保证。
        如需自动重试（执行失败时反馈 LLM 修正），可在 sql_coder_node
        中集成 sql_coder.generate_and_execute_sql 函数。

    参数:
        state: 当前 Agent 全局状态，需包含 generated_sql

    返回:
        成功时：包含 query_result、query_columns 和 stage
        失败时：额外设置 error_message 描述失败原因
    """
    engine = get_engine()
    sql = state.get("generated_sql", "")

    if not sql:
        logger.warning("[Executor] 无可执行的 SQL")
        return {
            "error_message": "无可执行的 SQL",
            "stage": "executed",
        }

    logger.info("[Executor] 执行 SQL: %s", sql[:120])

    try:
        result = await execute_sql(engine, sql)

        if not result["success"]:
            logger.error("[Executor] SQL 执行失败: %s", result["error"])
            return {
                "query_result": [],
                "query_columns": [],
                "error_message": f"SQL 执行失败: {result['error']}",
                "stage": "executed",
            }

        rows = result["data"]
        columns = list(rows[0].keys()) if rows else []

        logger.info("[Executor] 查询完成，返回 %d 行数据", len(rows))

        return {
            "query_result": rows,
            "query_columns": columns,
            "stage": "executed",
        }
    except Exception as exc:
        logger.exception("[Executor] SQL 执行异常")
        return {
            "query_result": [],
            "query_columns": [],
            "error_message": f"SQL 执行异常: {str(exc)}",
            "stage": "executed",
        }


async def analyst_node(state: AgentState) -> dict:
    """
    Analyst 节点 —— 对 SQL 查询结果进行统计分析与洞察生成。

    调用 Analyst Agent 对查询返回的数据做数值统计（计数、求和、
    均值、最大最小值等）并生成自然语言洞察和异常检测结果。
    分析失败不阻塞流程：异常时仅设置 error_message 而不中断。

    参数:
        state: 当前 Agent 全局状态，需包含 user_question、generated_sql、
               query_result、query_columns

    返回:
        包含 analysis_text 和 stage 的部分状态更新
    """
    query_result = state.get("query_result", [])
    query_columns = state.get("query_columns", [])
    user_question = state.get("user_question", "")
    sql = state.get("generated_sql", "")

    # 查询结果为空时跳过分析
    if not query_result or not query_columns:
        logger.info("[Analyst] 查询结果为空，跳过数据分析")
        return {"stage": "analyzed"}

    try:
        logger.info(
            "[Analyst] 开始分析结果: %d 行 %d 列",
            len(query_result),
            len(query_columns),
        )
        result = await analyze_results(
            question=user_question,
            sql=sql,
            data=query_result,
            columns=query_columns,
        )

        # 将洞察列表拼接为自然语言文本，写入 analysis_text
        insights = result.get("insights", [])
        anomalies = result.get("anomalies", [])
        parts = []
        if result.get("summary"):
            parts.append(result["summary"])
        if insights:
            parts.append("洞察: " + "; ".join(insights))
        if anomalies:
            parts.append("异常: " + "; ".join(anomalies))
        analysis_text = "\n".join(parts)

        logger.info("[Analyst] 分析完成: %d 条洞察, %d 个异常", len(insights), len(anomalies))

        return {
            "analysis_text": analysis_text,
            "stage": "analyzed",
        }
    except Exception as exc:
        # 分析失败不中断流程，仅记录错误信息
        logger.exception("[Analyst] 数据分析失败")
        return {
            "error_message": f"数据分析失败: {str(exc)}",
            "stage": "analyzed",
        }


async def reporter_node(state: AgentState) -> dict:
    """
    Reporter 节点 —— 根据查询结果生成 ECharts 图表配置。

    调用 Reporter Agent 根据数据特征自动选择图表类型（柱状图/
    饼图/折线图）并生成前端渲染所需的完整 ECharts option JSON。
    图表生成失败不阻塞流程：异常时仅设置 error_message 而不中断。

    参数:
        state: 当前 Agent 全局状态，需包含 user_question、
               query_result、query_columns

    返回:
        包含 chart_config 和 stage 的部分状态更新
    """
    query_result = state.get("query_result", [])
    query_columns = state.get("query_columns", [])
    user_question = state.get("user_question", "")

    # 查询结果为空时跳过图表生成
    if not query_result or not query_columns:
        logger.info("[Reporter] 查询结果为空，跳过图表生成")
        return {"stage": "reported"}

    try:
        logger.info("[Reporter] 开始生成图表配置")
        result = await generate_chart_config(
            question=user_question,
            data=query_result,
            columns=query_columns,
        )

        logger.info("[Reporter] 图表生成完成: type=%s", result.get("chart_type", "unknown"))

        return {
            "chart_config": result if result.get("chart_type") != "none" else None,
            "stage": "reported",
        }
    except Exception as exc:
        # 图表生成失败不中断流程，仅记录错误信息
        logger.exception("[Reporter] 图表生成失败")
        return {
            "error_message": f"图表生成失败: {str(exc)}",
            "stage": "reported",
        }


async def rag_node(state: AgentState) -> dict:
    """
    RAG 检索节点 —— 处理帮助咨询类问题。

    当用户意图为 ask_help 时，Orchestrator 会将请求路由到此节点。
    当前为占位实现，后续将对接 Milvus 向量数据库进行知识库检索，
    返回相关文档作为分析结果。

    参数:
        state: 当前 Agent 全局状态

    返回:
        包含 analysis_text 和 stage 的部分状态更新
    """
    logger.info("[RAGAgent] RAG 检索阶段（当前为占位实现）")
    return {
        "analysis_text": "RAG 检索功能开发中",
        "stage": "rag_done",
    }


async def finish_node(state: AgentState) -> dict:
    """
    结束节点 —— 标记工作流执行完毕。

    作为 Graph 的最终节点，将 stage 设置为 "finished" 以表示整个
    Multi-Agent 协作流程已完成。此节点连接到 END 终止符。

    参数:
        state: 当前 Agent 全局状态

    返回:
        包含 stage 的部分状态更新
    """
    logger.info("[Finish] 工作流执行完毕，stage=%s", state.get("stage", "unknown"))
    return {"stage": "finished"}

# ================================================================
# 检查点管理（应用生命周期级别）
# ================================================================

_checkpointer = None    # 全局检查点实例
_redis_cm = None        # Redis 异步上下文管理器引用（用于关闭时清理）


async def init_checkpointer():
    """
    在应用启动时初始化检查点保存器。
    必须在 async 环境（FastAPI lifespan）中调用。

    Redis 检查点 API 说明：
        AsyncRedisSaver.from_conn_string(url) 返回异步上下文管理器，
        需要通过 async with 进入上下文后才能拿到 BaseCheckpointSaver 实例。
    """
    global _checkpointer, _redis_cm
    try:
        from langgraph.checkpoint.redis import AsyncRedisSaver
        from app.core.config import settings

        # 进入异步上下文，获取真正的 saver 实例
        _redis_cm = AsyncRedisSaver.from_conn_string(settings.REDIS_URL)
        _checkpointer = await _redis_cm.__aenter__()

        logger.info("[Workflow] Redis 检查点初始化成功: %s", settings.REDIS_URL)
    except (ImportError, Exception) as exc:
        logger.warning(
            "[Workflow] Redis 检查点不可用 (%s)，回退到 MemorySaver",
            str(exc),
        )
        from langgraph.checkpoint.memory import InMemorySaver
        _checkpointer = InMemorySaver()


async def close_checkpointer():
    """
    在应用关闭时清理检查点资源。
    必须在 async 环境（FastAPI lifespan）中调用。
    """
    global _checkpointer, _redis_cm
    if _redis_cm is not None:
        try:
            await _redis_cm.__aexit__(None, None, None)
            logger.info("[Workflow] Redis 检查点已关闭")
        except Exception as exc:
            logger.warning("[Workflow] 关闭 Redis 检查点异常: %s", exc)
        _redis_cm = None
    _checkpointer = None
# ================================================================
# Graph 构建与编译
# ================================================================

# 全局编译后的 Graph 单例
_graph = None


def get_graph():
    """
    获取已编译的 LangGraph 工作流实例（全局单例）。

    首次调用时：
        1. 构建 StateGraph 并注册所有节点和边
        2. 创建检查点保存器（优先 Redis，回退 MemorySaver）
        3. 编译 Graph 并缓存为全局单例

    后续调用直接返回缓存实例，避免重复编译开销。

    检查点策略：
        - 优先尝试 Redis AsyncRedisSaver（支持持久化、分布式、中断恢复）
        - 若 Redis 不可用（依赖未安装或连接失败），回退到 MemorySaver
        - 检查点是 interrupt() 中断/恢复机制的必要依赖

    返回:
        编译好的 StateGraph 实例，可通过 .invoke() / .astream() 执行
    """
    global _graph
    if _graph is not None:
        return _graph

    # ── 构建状态图 ────────────────────────────────────
    builder = StateGraph(AgentState)

    # 注册所有节点
    builder.add_node("orchestrator", orchestrator_node)
    builder.add_node("misc_agent", misc_node)
    builder.add_node("schema_agent", schema_node)
    builder.add_node("sql_coder", sql_coder_node)
    builder.add_node("security", security_node)
    builder.add_node("execute_sql", execute_node)
    builder.add_node("analyst", analyst_node)
    builder.add_node("reporter", reporter_node)
    builder.add_node("rag_agent", rag_node)
    builder.add_node("finish", finish_node)

    # ── 注册边（定义节点间的流转关系） ────────────────

    # 入口：orchestrator 为起始节点
    builder.set_entry_point("orchestrator")

    # orchestrator → 条件路由：根据意图分发到 schema_agent 或 rag_agent
    builder.add_conditional_edges(
        "orchestrator",
        route_orchestrator,
        {
            "schema_agent": "schema_agent",
            "rag_agent": "rag_agent",
            "misc_agent": "misc_agent",
        },
    )

    # schema_agent → sql_coder（线性流转：加载表结构后生成 SQL）
    builder.add_edge("schema_agent", "sql_coder")

    # sql_coder → security（线性流转：生成 SQL 后进行安全审核）
    builder.add_edge("sql_coder", "security")

    # security → 条件路由：根据审核结果决定执行还是终止
    builder.add_conditional_edges(
        "security",
        route_security,
        {
            "execute_sql": "execute_sql",
            "finish": "finish",
        },
    )

    # execute_sql → analyst（查询执行完毕后进入数据分析节点）
    builder.add_edge("execute_sql", "analyst")

    # analyst → reporter（数据分析完毕后进入图表生成节点）
    builder.add_edge("analyst", "reporter")

    # reporter → finish（图表生成完毕后进入结束节点）
    builder.add_edge("reporter", "finish")

    # rag_agent → finish（线性流转：RAG 检索完毕后进入结束节点）
    builder.add_edge("rag_agent", "finish")

    # finish → END（终止节点，Graph 执行结束）
    builder.add_edge("finish", END)

    # ✅ 使用全局已初始化的检查点实例
    if _checkpointer is None:
        logger.warning("[Workflow] 检查点未初始化，使用 None（不支持中断恢复）")

    _graph = builder.compile(checkpointer=_checkpointer)
    logger.info("[Workflow] LangGraph 工作流编译完成")
    return _graph


