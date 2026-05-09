"""
Agent 模块 —— 多智能体协作，负责元数据提取、SQL 生成与执行、数据分析和报表生成等核心任务
"""
from app.agents.orchestrator import analyze_intent, route_by_intent
from app.agents.rag_agent import retrieve_knowledge, answer_with_rag, enhance_schema_with_rag
from app.agents.schema_agent import get_table_schemas, filter_relevant_tables
from app.agents.sql_coder import generate_sql, execute_sql, generate_and_execute_sql
from app.agents.security import classify_sql, mask_sensitive_data
from app.agents.analyst import analyze_results
from app.agents.reporter import generate_chart_config, generate_excel
from app.agents.misc_agent import misc_agent

__all__ = [
    "analyze_intent",
    "route_by_intent",
    "retrieve_knowledge",
    "answer_with_rag",
    "enhance_schema_with_rag",
    "get_table_schemas",
    "filter_relevant_tables",
    "generate_sql",
    "execute_sql",
    "generate_and_execute_sql",
    "classify_sql",
    "mask_sensitive_data",
    "analyze_results",
    "generate_chart_config",
    "generate_excel",
    "misc_agent",
]
