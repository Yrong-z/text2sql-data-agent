from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import get_llm_client
from app.agent.state import DataAgentState
from app.core.log import logger
from app.entities.column_info import ColumnInfo
from app.prompt.prompt_loader import load_prompt


async def recall_column(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    step = "召回字段"

    writer({"type": "progress", "step": step, "status": "running"})

    keywords = state["keywords"]
    query = state["query"]

    column_qdrant_repository = runtime.context["column_qdrant_repository"]
    embedding_client = runtime.context["embedding_client"]

    try:
        prompt = PromptTemplate(
            template=load_prompt("extend_keywords_for_column_recall"),
            input_variables=["query"],
        )

        output_parser = JsonOutputParser()
        chain = prompt | get_llm_client() | output_parser

        result = await chain.ainvoke({"query": query})
        keywords = list(set(keywords + result))

        column_info_map: dict[str, ColumnInfo] = {}

        for keyword in keywords:
            embedding = await embedding_client.aembed_query(keyword)

            current_column_infos: list[ColumnInfo] = (
                await column_qdrant_repository.search(
                    embedding,
                    score_threshold=0.6,
                    limit=20,
                )
            )

            for column_info in current_column_infos:
                if column_info.id not in column_info_map:
                    column_info_map[column_info.id] = column_info

        retrieved_column_infos = list(column_info_map.values())

        writer({"type": "progress", "step": step, "status": "success"})
        logger.info(f"检索到字段信息: {list(column_info_map.keys())}")

        return {"retrieved_columns": retrieved_column_infos}

    except Exception as e:
        writer({"type": "progress", "step": step, "status": "error"})
        logger.exception(f"召回字段失败: {e}")
        raise
