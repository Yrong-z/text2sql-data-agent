from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.nodes.sql_utils import clean_sql
from app.agent.state import DataAgentState
from app.core.log import logger


async def validate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """
    校验生成 SQL 是否可执行。

    业务语义：
    1. 该节点不直接中断整条链路，而是把校验结果写入 state["error"]。
    2. 校验成功返回 {"sql": cleaned_sql, "error": None}，后续进入 run_sql。
    3. 校验失败返回 {"error": "..."}，后续进入 correct_sql。
    4. 校验前先清洗 SQL，保证与 run_sql 使用相同的 SQL 文本。
    """

    writer = runtime.stream_writer
    step = "验证SQL"

    writer({"type": "progress", "step": step, "status": "running"})

    dw_mysql_repository = runtime.context["dw_mysql_repository"]
    raw_sql = state.get("sql")

    try:
        if not raw_sql:
            raise ValueError("SQL为空，无法验证")

        sql = clean_sql(raw_sql)
        await dw_mysql_repository.validate_sql(sql)

        writer({"type": "progress", "step": step, "status": "success"})
        logger.info(f"SQL验证成功: {sql}")

        return {
            "sql": sql,
            "error": None,
        }

    except Exception as e:
        writer({"type": "progress", "step": step, "status": "error"})
        logger.exception(f"SQL验证失败: sql={raw_sql}, error={e}")
        return {"error": str(e)}
