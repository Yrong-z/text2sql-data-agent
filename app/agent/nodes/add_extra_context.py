from datetime import datetime

from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, DateInfoState
from app.core.log import logger


async def add_extra_context(
    state: DataAgentState,
    runtime: Runtime[DataAgentContext],
):

    writer = runtime.stream_writer
    step = "添加额外上下文信息"

    writer({"type": "progress", "step": step, "status": "running"})

    try:
        dw_mysql_repository = runtime.context["dw_mysql_repository"]

        today = datetime.today()

        date_info = DateInfoState(
            date=today.strftime("%Y-%m-%d"),
            weekday=today.strftime("%A"),
            quarter=f"Q{(today.month - 1) // 3 + 1}",
        )

        db_info = await dw_mysql_repository.get_db_info()

        writer({"type": "progress", "step": step, "status": "success"})

        logger.info(f"添加额外上下文信息成功: date_info={date_info}, db_info={db_info}")

        return {
            "date_info": date_info,
            "db_info": db_info,
        }

    except Exception as e:
        writer({"type": "progress", "step": step, "status": "error"})
        logger.exception(f"添加额外上下文信息失败: {e}")
        raise