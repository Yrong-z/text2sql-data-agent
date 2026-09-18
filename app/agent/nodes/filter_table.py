import yaml

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import get_llm_client
from app.agent.state import DataAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


async def filter_table(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    step = "过滤表信息"

    writer({"type": "progress", "step": step, "status": "running"})

    query = state["query"]
    table_infos = state.get("table_infos", [])

    try:
        prompt = PromptTemplate(
            template=load_prompt("filter_table_info"),
            input_variables=["query", "table_infos"],
        )

        output_parser = JsonOutputParser()
        chain = prompt | get_llm_client() | output_parser

        result = await chain.ainvoke(
            {
                "query": query,
                "table_infos": yaml.dump(
                    table_infos,
                    allow_unicode=True,
                    sort_keys=False,
                ),
            }
        )

        filtered_table_infos = []

        for table_info in table_infos:
            table_name = table_info["name"]

            if table_name not in result:
                continue

            selected_columns = result[table_name]

            filtered_columns = [
                column_info
                for column_info in table_info["columns"]
                if column_info["name"] in selected_columns
            ]

            if not filtered_columns:
                continue

            filtered_table_infos.append(
                {
                    **table_info,
                    "columns": filtered_columns,
                }
            )

        writer({"type": "progress", "step": step, "status": "success"})
        logger.info(
            f"过滤后的表信息: {[table_info['name'] for table_info in filtered_table_infos]}"
        )

        return {"table_infos": filtered_table_infos}

    except Exception as e:
        writer({"type": "progress", "step": step, "status": "error"})
        logger.exception(f"过滤表信息失败: {e}")
        raise
