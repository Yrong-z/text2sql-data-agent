import re

import yaml
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import get_llm_client
from app.agent.state import DataAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


def _clean_sql(sql: str) -> str:
    if not sql:
        return sql

    sql = sql.strip()
    sql = re.sub(r"^```(?:sql)?\s*", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\s*```$", "", sql)
    return sql.strip()


async def generate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    step = "生成SQL"

    writer({"type": "progress", "step": step, "status": "running"})

    query = state["query"]
    table_infos = state.get("table_infos", [])
    metric_infos = state.get("metric_infos", [])
    date_info = state.get("date_info", {})
    db_info = state.get("db_info", {})

    try:
        prompt = PromptTemplate(
            template=load_prompt("generate_sql"),
            input_variables=[
                "query",
                "table_infos",
                "metric_infos",
                "date_info",
                "db_info",
            ],
        )

        output_parser = StrOutputParser()
        chain = prompt | get_llm_client() | output_parser

        result = await chain.ainvoke(
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
            }
        )

        sql = _clean_sql(result)

        writer({"type": "progress", "step": step, "status": "success"})
        writer({"type": "sql_generated", "data": {"sql": sql}})
        logger.info(f"生成的SQL: {sql}")

        return {"sql": sql}

    except Exception as e:
        writer({"type": "progress", "step": step, "status": "error"})
        logger.exception(f"生成SQL失败: {e}")
        raise
