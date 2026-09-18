# app/db/init_db.py
from sqlalchemy.ext.asyncio import AsyncEngine
from app.models.base import Base

# 显式导入所有模型，确保它们被注册到 Base.metadata
from app.models.table_info import TableInfoMySQL          # noqa
from app.models.column_info import ColumnInfoMySQL        # noqa
# 如果你还有 metric_info / column_metric 等模型，也请导入
# from app.models.metric_info import MetricInfoMySQL      # noqa
# from app.models.column_metric import ColumnMetricMySQL  # noqa

async def create_all_tables(engine: AsyncEngine) -> None:
    """根据所有已导入的 ORM 模型，在数据库中创建缺失的表。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)