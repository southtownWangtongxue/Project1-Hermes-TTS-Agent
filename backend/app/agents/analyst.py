"""
Analyst Agent - 数据分析师
接收 SQL 执行结果集，进行统计分析并生成自然语言洞察
"""
import json
import statistics
import math

from app.core.config import settings
from app.core.llm import get_llm
from app.utils.json_encoder import CustomEncoder


def _basic_stats(data: list[dict], columns: list[str]) -> dict:
    """
    纯 Python 计算基本统计量（不调 LLM）。

    对数值列计算 sum/avg/min/max，对文本列计算唯一值数量，
    并检测极端值（超过均值 ± 2 倍标准差的视为异常）。

    参数:
        data: 查询结果行列表，每行为一个字典
        columns: 列名列表

    返回:
        {
            "row_count": int,
            "numeric_stats": {列名: {"sum": float, "avg": float, "min": float, "max": float}},
            "text_stats": {列名: {"unique_count": int}},
            "outliers": {列名: [异常值列表]},
        }
    """
    numeric_stats: dict = {}
    text_stats: dict = {}
    outliers: dict = {}

    # 识别数值列和文本列
    numeric_cols: list[str] = []
    text_cols: list[str] = []

    for col in columns:
        # 取第一行有效数据判断列类型
        values = [row.get(col) for row in data if row.get(col) is not None]
        if not values:
            # 整列全为空，归为文本列
            text_cols.append(col)
            continue

        sample = values[0]
        if isinstance(sample, (int, float)) and not isinstance(sample, bool):
            numeric_cols.append(col)
        else:
            text_cols.append(col)

    # 对数值列计算统计量
    for col in numeric_cols:
        values = []
        for row in data:
            v = row.get(col)
            if v is not None:
                try:
                    values.append(float(v))
                except (ValueError, TypeError):
                    continue

        if not values:
            continue

        stat = {
            "sum": round(sum(values), 4),
            "avg": round(statistics.mean(values), 4),
            "min": round(min(values), 4),
            "max": round(max(values), 4),
        }

        # 只有多于 1 个数据点时才计算标准差
        if len(values) > 1:
            stat["std"] = round(statistics.stdev(values), 4)
        else:
            stat["std"] = 0

        numeric_stats[col] = stat

        # 检测极端值（超过均值 ± 2 倍标准差的视为异常）
        if stat["std"] > 0:
            mean = stat["avg"]
            std = stat["std"]
            lower = mean - 2 * std
            upper = mean + 2 * std
            col_outliers = []
            for row in data:
                v = row.get(col)
                if v is not None:
                    try:
                        fv = float(v)
                    except (ValueError, TypeError):
                        continue
                    if fv < lower or fv > upper:
                        col_outliers.append({col: v, "value": fv})
            if col_outliers:
                outliers[col] = col_outliers

    # 对文本列计算唯一值数量
    for col in text_cols:
        unique_values = set()
        for row in data:
            v = row.get(col)
            if v is not None:
                unique_values.add(str(v))
        text_stats[col] = {"unique_count": len(unique_values)}

    return {
        "row_count": len(data),
        "numeric_stats": numeric_stats,
        "text_stats": text_stats,
        "outliers": outliers,
    }


async def analyze_results(
    question: str, sql: str, data: list[dict], columns: list[str]
) -> dict:
    """
    对查询结果做数值统计分析，生成自然语言洞察。

    流程：
    1. 调用 _basic_stats 进行纯 Python 基础统计
    2. 将基础统计结果 + 前 10 行数据 + 用户原始问题发给 LLM
    3. LLM 以数据分析师身份生成洞察并返回 JSON

    参数:
        question: 用户原始问题
        sql: 最终执行的 SQL 语句
        data: 查询结果行列表
        columns: 列名列表

    返回:
        {
            "summary": str,           # 数据概览
            "stats": dict,            # 基本统计量
            "insights": list[str],    # 洞察列表
            "anomalies": list[str],   # 异常点
        }
    """
    # ── 第一步：基础统计（不调 LLM） ──────────────────────
    stats = _basic_stats(data, columns)

    # 构建数据概览摘要
    row_count = stats["row_count"]
    overview_parts = [f"共查询到 {row_count} 条记录"]

    for col_name, col_stat in stats["numeric_stats"].items():
        overview_parts.append(
            f"{col_name} 合计 {col_stat['sum']}，"
            f"均值 {col_stat['avg']}，"
            f"最小值 {col_stat['min']}，"
            f"最大值 {col_stat['max']}"
        )

    summary = "；".join(overview_parts)

    # 如果没有数据，直接返回空结果
    if row_count == 0:
        return {
            "summary": "查询结果为空，未能获取到任何数据。",
            "stats": stats,
            "insights": [],
            "anomalies": [],
        }

    # ── 第二步：LLM 增强分析 ──────────────────────────────
    # 取前 10 行数据供 LLM 参考
    sample_data = data[:10]

    client = get_llm()

    system_prompt = (
        "你是一个专业的数据分析师。"
        "根据提供的查询结果和基础统计信息，生成有价值的数据洞察和异常检测。\n\n"
        "严格要求：\n"
        "1. 只返回 JSON 格式，不要包含任何其他文字或 markdown 标记\n"
        "2. summary 字段：用一两句话概括数据的整体情况\n"
        "3. insights 字段：列出 2-5 条具体的数据洞察（如排名、占比、趋势等）\n"
        "4. anomalies 字段：列出数据中的异常点或需要关注的问题\n"
        "5. 返回的 JSON 必须是合法的，使用双引号\n"
        "6. 如果无法生成有意义的洞察，相应字段返回空列表"
    )

    # 将基础统计格式化为易读字符串
    stats_text = json.dumps(stats, ensure_ascii=False, indent=2)
    sample_text = json.dumps(sample_data, ensure_ascii=False, indent=2,cls=CustomEncoder)

    user_message = (
        f"## 用户问题\n\n{question}\n\n"
        f"## 执行的 SQL\n\n```sql\n{sql}\n```\n\n"
        f"## 基础统计结果\n\n```json\n{stats_text}\n```\n\n"
        f"## 前 {len(sample_data)} 行数据\n\n```json\n{sample_text}\n```\n\n"
        "请分析以上数据，生成洞察和异常检测结果："
    )

    response = await client.chat.completions.create(
        model=settings.LLM_MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
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
        # LLM 返回格式异常时使用基础统计结果兜底
        return {
            "summary": summary,
            "stats": stats,
            "insights": [],
            "anomalies": [],
        }

    # 合并基础统计量与 LLM 生成的分析
    return {
        "summary": llm_result.get("summary", summary),
        "stats": stats,
        "insights": llm_result.get("insights", []),
        "anomalies": llm_result.get("anomalies", []),
    }
