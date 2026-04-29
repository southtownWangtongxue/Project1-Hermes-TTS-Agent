"""
Reporter Agent - 报表生成专家
根据数据特征推荐图表类型，生成 ECharts JSON 配置
"""
import json

from app.core.config import settings
from app.core.llm import get_llm


def _recommend_chart_type(columns: list[str], data: list[dict]) -> str:
    """
    纯规则的基础图表推荐（不调 LLM），作为 LLM 推荐前的默认值。

    规则：
    - 有日期列 + 数值列 → "line"（折线图）
    - 仅分类列 + 数值列 → "bar"（柱状图）
    - 一维分类 + 一维数值 → "pie"（饼图）
    - 双数值列 → "scatter"（散点图）
    - 无法判断时默认返回 "bar"

    参数:
        columns: 列名列表
        data: 查询结果行列表

    返回:
        图表类型字符串，取值为 "line" | "bar" | "pie" | "scatter"
    """
    if not columns or not data:
        return "bar"

    # 识别列类型
    numeric_cols: list[str] = []
    date_cols: list[str] = []
    text_cols: list[str] = []

    # 日期相关的列名关键词
    date_keywords = ["date", "time", "日期", "时间", "year", "month", "day",
                     "年", "月", "日", "created", "updated", "create_time",
                     "update_time", "datetime", "timestamp"]

    for col in columns:
        col_lower = col.lower()
        # 判断是否为日期列（按列名关键词匹配）
        is_date = any(kw in col_lower for kw in date_keywords)
        if is_date:
            date_cols.append(col)
            continue

        # 判断是否为数值列（取第一行非空值判断）
        sample_values = [row.get(col) for row in data if row.get(col) is not None]
        if sample_values and isinstance(sample_values[0], (int, float)):
            numeric_cols.append(col)
        else:
            text_cols.append(col)

    # 按规则推荐图表类型
    if len(date_cols) >= 1 and len(numeric_cols) >= 1:
        # 时间序列 + 数值 → 折线图
        return "line"
    elif len(text_cols) >= 1 and len(numeric_cols) >= 2:
        # 双数值列 → 散点图
        return "scatter"
    elif len(text_cols) >= 1 and len(numeric_cols) == 1:
        # 一维分类 + 一维数值 → 饼图（数据量少时）或柱状图
        if len(data) <= 10:
            return "pie"
        else:
            return "bar"
    elif len(text_cols) >= 1 and len(numeric_cols) >= 1:
        # 分类对比 → 柱状图
        return "bar"
    elif len(numeric_cols) >= 2:
        # 双数值列（无文本列）→ 散点图
        return "scatter"

    # 默认为柱状图
    return "bar"


async def generate_chart_config(
    question: str, data: list[dict], columns: list[str]
) -> dict:
    """
    调用 LLM 分析数据特征，推荐图表类型并生成 ECharts 配置。

    参数:
        question: 用户原始问题
        data: 查询结果行列表
        columns: 列名列表

    返回:
        {
            "chart_type": str,          # "line" | "bar" | "pie" | "scatter"
            "chart_title": str,         # 图表标题
            "echarts_config": dict,     # 完整的 ECharts option JSON 配置
        }
    """
    # ── 步骤 1：规则兜底推荐 ─────────────────────────────
    fallback_type = _recommend_chart_type(columns, data)

    # ── 步骤 2：LLM 生成图表配置 ─────────────────────────
    # 取前 20 行数据供 LLM 分析
    sample_data = data[:20]

    client = get_llm()

    system_prompt = (
        "你是一个专业的 ECharts 报表配置专家。"
        "根据提供给您的查询结果数据，分析数据特征并选择合适的图表类型，"
        "然后生成完整的 ECharts option JSON 配置。\n\n"
        "图表选择规则：\n"
        "- 时间序列 + 数值 → 折线图 (line)\n"
        "- 分类对比 → 柱状图 (bar)\n"
        "- 占比分布 → 饼图 (pie)\n"
        "- 双数值列 → 散点图 (scatter)\n\n"
        "ECharts 配置要求：\n"
        "- 必须包含 title、xAxis、yAxis、series 等基本元素\n"
        "- 饼图无需 xAxis/yAxis\n"
        "- tooltip 和 legend 默认开启\n"
        "- 颜色使用现代简洁风格\n"
        "- 数据点数量超过 15 个的折线图/柱状图建议添加 dataZoom\n\n"
        "严格要求：\n"
        "1. 只返回 JSON 格式，不要包含任何其他文字或 markdown 标记\n"
        "2. 返回的 JSON 必须包含三个字段：chart_type、chart_title、echarts_config\n"
        "3. echarts_config 必须是合法且完整的 ECharts option 对象\n"
        "4. 所有字段使用双引号"
    )

    sample_text = json.dumps(sample_data, ensure_ascii=False, indent=2)
    columns_text = json.dumps(columns, ensure_ascii=False)

    user_message = (
        f"## 用户问题\n\n{question}\n\n"
        f"## 数据列名\n\n{columns_text}\n\n"
        f"## 查询结果（前 {len(sample_data)} 行）\n\n```json\n{sample_text}\n```\n\n"
        f"## 规则推荐兜底\n\n{fallback_type}\n\n"
        "请分析数据特征，推荐图表类型并生成 ECharts 配置："
    )

    response = await client.chat.completions.create(
        model=settings.LLM_MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
    )

    # 解析 LLM 返回的 JSON
    raw_content = response.choices[0].message.content.strip()
    try:
        # 去除可能的 markdown 代码块标记
        if raw_content.startswith("```"):
            lines = raw_content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw_content = "\n".join(lines).strip()

        llm_result = json.loads(raw_content)
    except json.JSONDecodeError:
        # LLM 返回格式异常时使用规则兜底 + 空配置
        return {
            "chart_type": fallback_type,
            "chart_title": "数据可视化",
            "echarts_config": {},
        }

    return {
        "chart_type": llm_result.get("chart_type", fallback_type),
        "chart_title": llm_result.get("chart_title", "数据可视化"),
        "echarts_config": llm_result.get("echarts_config", {}),
    }


async def generate_excel(
    data: list[dict], columns: list[str], filename: str
) -> str:
    """
    占位函数：Excel 导出功能将在阶段 4 实现。

    参数:
        data: 查询结果行列表
        columns: 列名列表
        filename: 目标文件名

    返回:
        提示信息字符串
    """
    return "Excel 导出功能将在阶段 4 实现"
