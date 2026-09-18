# app/api/routers/query_router.py

from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse

from app.api.dependencies import get_query_service
from app.api.schemas.query_schema import QuerySchema
from app.services.query_service import QueryService

query_router = APIRouter()


@query_router.post("/api/query")
async def query(
    query_schema: QuerySchema,
    query_service: QueryService = Depends(get_query_service),
):
    """
    问数查询接口

    请求体:
    {
        "query": "统计去年各地区的销售总额"
    }

    返回:
    SSE 流式数据:
    data: {"type": "progress", "step": "抽取关键字", "status": "running"}

    data: {"type": "result", "data": [...]}
    """

    return StreamingResponse(
        query_service.query(query_schema.query),
        media_type="text/event-stream",
    )