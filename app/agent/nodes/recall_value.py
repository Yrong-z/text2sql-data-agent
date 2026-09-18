from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import get_llm_client
from app.agent.state import DataAgentState
from app.core.log import logger
from app.entities.value_info import ValueInfo
from app.prompt.prompt_loader import load_prompt


async def recall_value(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    step = "召回字段值"

    writer({"type": "progress", "step": step, "status": "running"})

    query = state["query"]
    keywords = state["keywords"]

    value_es_repository = runtime.context["value_es_repository"]

    try:
        prompt = PromptTemplate(
            template=load_prompt("extend_keywords_for_value_recall"),
            input_variables=["query"],
        )
        output_parser = JsonOutputParser()
        chain = prompt | get_llm_client() | output_parser

        result = await chain.ainvoke({"query": query})

        if isinstance(result, dict):
            if "keywords" in result and isinstance(result["keywords"], list):
                result = result["keywords"]
            else:
                result = list(result.values())

        if not isinstance(result, list):
            result = [str(result)]

        recall_keywords = list(set(keywords + result))
        logger.info(f"召回字段值扩展关键词: {recall_keywords}")

        values_map: dict[str, ValueInfo] = {}

        for keyword in recall_keywords:
            values: list[ValueInfo] = await value_es_repository.search(keyword)

            for value in values:
                if value.id not in values_map:
                    values_map[value.id] = value

        retrieved_values = list(values_map.values())

        writer({"type": "progress", "step": step, "status": "success"})
        logger.info(f"召回字段取值: {list(values_map.keys())}")

        return {"retrieved_values": retrieved_values}

    except Exception as e:
        writer({"type": "progress", "step": step, "status": "error"})
        logger.exception(f"召回字段值失败: {e}")
        raise
