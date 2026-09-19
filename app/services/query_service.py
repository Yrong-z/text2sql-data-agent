
import json
from openai import APIConnectionError, APITimeoutError, AuthenticationError

from app.agent.context import DataAgentContext
from app.agent.graph import graph
from app.agent.state import DataAgentState


class QueryService:
    def __init__(
        self,
        embedding_client,
        column_qdrant_repository,
        value_es_repository,
        metric_qdrant_repository,
        meta_mysql_repository,
        dw_mysql_repository,
    ):
        self.embedding_client = embedding_client
        self.column_qdrant_repository = column_qdrant_repository
        self.value_es_repository = value_es_repository
        self.metric_qdrant_repository = metric_qdrant_repository
        self.meta_mysql_repository = meta_mysql_repository
        self.dw_mysql_repository = dw_mysql_repository

    async def query(self, query: str):
        context = DataAgentContext(
            embedding_client=self.embedding_client,
            column_qdrant_repository=self.column_qdrant_repository,
            value_es_repository=self.value_es_repository,
            metric_qdrant_repository=self.metric_qdrant_repository,
            meta_mysql_repository=self.meta_mysql_repository,
            dw_mysql_repository=self.dw_mysql_repository,
        )

        state = DataAgentState(query=query)

        try:
            async for chunk in graph.astream(
                input=state,
                context=context,
                stream_mode="custom",
            ):
                # print(">>> graph chunk:", chunk)
                yield f"data: {json.dumps(chunk, ensure_ascii=False, default=str)}\n\n"

        except Exception as e:
            if isinstance(e, APITimeoutError):
                message = "模型服务响应超时，请稍后重试"
            elif isinstance(e, APIConnectionError):
                message = "无法连接模型服务，请检查后端网络连接后重试"
            elif isinstance(e, AuthenticationError):
                message = "模型服务认证失败，请检查 API Key 配置"
            else:
                message = str(e) or "查询处理失败"
            error_data = {
                "type": "error",
                "message": message,
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False, default=str)}\n\n"
