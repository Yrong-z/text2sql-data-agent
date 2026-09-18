from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.nodes.sql_utils import clean_sql
from app.agent.state import DataAgentState
from app.core.log import logger


async def run_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """
    执行最终 SQL。

    业务约束：
    1. 这里只执行已生成并完成校验的 SQL。
    2. 如果 validate_sql 失败，链路会先进入 correct_sql，再回到这里执行修正后的 SQL。
    3. 执行前和校验前使用同一套 SQL 清洗逻辑，避免行为不一致。
    4. 执行异常继续上抛，由 QueryService 统一转换为 SSE error。
    """

    writer = runtime.stream_writer
    step = "执行SQL"

    writer({"type": "progress", "step": step, "status": "running"})

    sql = state.get("sql")
    dw_mysql_repository = runtime.context["dw_mysql_repository"]

    try:
        if not sql:
            raise ValueError("SQL为空，无法执行")

        sql = clean_sql(sql)
        result = await dw_mysql_repository.execute_sql(sql)

        writer({"type": "progress", "step": step, "status": "success"})
        writer({"type": "result", "data": result})

        logger.info(f"执行SQL成功: sql={sql}, result={result}")
        return {}

    except Exception as e:
        writer({"type": "progress", "step": step, "status": "error"})
        logger.exception(f"执行SQL失败: sql={sql}, error={e}")
        raise
