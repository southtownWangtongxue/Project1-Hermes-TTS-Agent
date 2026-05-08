"""
Misc Agent - 杂项助理
处理无法意图归类的问题
"""

from app.core.llm import get_langchain_llm
from app.utils.log_utils import log


async def misc_agent(user_question: str) -> dict:
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
    client = get_langchain_llm()

    system_prompt = (
        """
        你是系统的友好助手，专门处理“不在业务范围内”的用户问题。
        
        你的任务：  
        - 用户当前的问题无法归类为查询数据（query_data）、询问帮助（ask_help）或修改数据（write_data）  
        - 你不可生成 SQL 语句，不可调用知识库，也不可执行任何数据操作  
        - 你需要礼貌地告知用户：该问题超出了本系统的能力范围，并引导用户提出与系统功能相关的问题（如数据查询、使用帮助、数据更新等）
        
        回复风格：  
        - 语气友好、清晰、不冗余  
        - 可以举例说明系统能支持的问题类型  
        
        输出要求：  
        - 只输出回复文本，不要包含 JSON、代码块或额外说明  
        """
    )

    try:
        response = await client.ainvoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question},
            ]
        )
        log.info(f"misc_agent->content:{response.content}")
        return response

    except  Exception as e:
        # LLM 返回解析失败，默认按查询数据处理
        log.exception(f"misc_agent->Exception:{e}")
        return {"content": f"无法归类为查询数据{str(e)}"}
