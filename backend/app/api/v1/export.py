"""
文件导出接口
支持将查询结果导出为 Excel 或 CSV 格式
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import io
import csv
import json

router = APIRouter(prefix="/export", tags=["export"])


class ExportRequest(BaseModel):
    """导出请求体"""
    data: list[dict] = Field(..., description="要导出的数据行列表")
    columns: list[str] = Field(..., description="列名列表")
    format: str = Field(default="csv", description="导出格式: csv 或 excel")
    filename: str = Field(default="export", description="文件名（不含扩展名）")


@router.post("/csv", summary="导出为 CSV 格式")
async def export_csv(body: ExportRequest):
    """
    将查询结果导出为 CSV 文件并返回文件流。
    """
    output = io.StringIO()
    if body.columns:
        writer = csv.DictWriter(output, fieldnames=body.columns)
        writer.writeheader()
        writer.writerows(body.data)
    else:
        writer = csv.writer(output)
        for row in body.data:
            writer.writerow(row.values())

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={body.filename}.csv",
        },
    )


@router.post("/excel", summary="导出为 Excel 格式（占位）")
async def export_excel(body: ExportRequest):
    """
    Excel 导出功能将在后续迭代中实现（需要 openpyxl 库）。
    当前返回 CSV 作为降级方案。
    """
    return await export_csv(body)
