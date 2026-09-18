import yaml

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


async def filter_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    step = "过滤指标"

    writer({"type": "progress", "step": step, "status": "running"})

    query = state["query"]
    metric_infos = state.get("metric_infos", [])

    try:
        prompt = PromptTemplate(
            template=load_prompt("filter_metric_info"),
            input_variables=["query", "metric_infos"],
        )

        output_parser = JsonOutputParser()
        chain = prompt | llm | output_parser

        result = await chain.ainvoke(
            {
                "query": query,
                "metric_infos": yaml.dump(
                    metric_infos,
                    allow_unicode=True,
                    sort_keys=False,
                ),
            }
        )

        filtered_metric_infos = [
            metric_info
            for metric_info in metric_infos
            if metric_info["name"] in result
        ]

        writer({"type": "progress", "step": step, "status": "success"})
        logger.info(
            f"过滤后的指标: {[metric_info['name'] for metric_info in filtered_metric_infos]}"
        )

        return {"metric_infos": filtered_metric_infos}

    except Exception as e:
        writer({"type": "progress", "step": step, "status": "error"})
        logger.exception(f"过滤指标失败: {e}")
        raise
