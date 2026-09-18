import yaml

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import get_llm_client
from app.agent.state import DataAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


async def correct_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    step = "校正SQL"

    writer({"type": "progress", "step": step, "status": "running"})

    query = state["query"]
    sql = state["sql"]
    error = state["error"]

    table_infos = state["table_infos"]
    metric_infos = state["metric_infos"]
    date_info = state["date_info"]
    db_info = state["db_info"]

    try:
        prompt = PromptTemplate(
            template=load_prompt("correct_sql"),
            input_variables=[
                "query",
                "table_infos",
                "metric_infos",
                "date_info",
                "db_info",
                "sql",
                "error",
            ],
        )

        output_parser = StrOutputParser()
        chain = prompt | get_llm_client() | output_parser

        corrected_sql = await chain.ainvoke(
            {
                "query": query,
                "table_infos": yaml.dump(
                    table_infos,
                    allow_unicode=True,
                    sort_keys=False,
                ),
                "metric_infos": yaml.dump(
                    metric_infos,
                    allow_unicode=True,
                    sort_keys=False,
                ),
                "date_info": yaml.dump(
                    date_info,
                    allow_unicode=True,
                    sort_keys=False,
                ),
                "db_info": yaml.dump(
                    db_info,
                    allow_unicode=True,
                    sort_keys=False,
                ),
                "sql": sql,
                "error": error,
            }
        )

        corrected_sql = corrected_sql.strip()

        writer({"type": "progress", "step": step, "status": "success"})
        logger.info(f"校正后的SQL: {corrected_sql}")

        return {"sql": corrected_sql}

    except Exception as e:
        writer({"type": "progress", "step": step, "status": "error"})
        logger.exception(f"校正SQL失败: {e}")
        raise
