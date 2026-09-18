from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.column_info import ColumnInfo
from app.entities.column_metric import ColumnMetric
from app.entities.metric_info import MetricInfo
from app.entities.table_info import TableInfo

from app.models.column_info import ColumnInfoMySQL
from app.models.table_info import TableInfoMySQL

from app.repositories.mysql.meta.mappers.column_info_mapper import ColumnInfoMapper
from app.repositories.mysql.meta.mappers.column_metric_mapper import ColumnMetricMapper
from app.repositories.mysql.meta.mappers.metric_info_mapper import MetricInfoMapper
from app.repositories.mysql.meta.mappers.table_info_mapper import TableInfoMapper


class MetaMysqlRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_table_infos(self, table_infos: list[TableInfo]):
        for table_info in table_infos:
            model = TableInfoMapper.to_model(table_info)
            await self.session.merge(model)

    async def save_column_infos(self, column_infos: list[ColumnInfo]):
        for column_info in column_infos:
            model = ColumnInfoMapper.to_model(column_info)
            await self.session.merge(model)

    async def save_metric_infos(self, metric_infos: list[MetricInfo]):
        for metric_info in metric_infos:
            model = MetricInfoMapper.to_model(metric_info)
            await self.session.merge(model)

    async def save_column_metrics(self, column_metrics: list[ColumnMetric]):
        for column_metric in column_metrics:
            model = ColumnMetricMapper.to_model(column_metric)
            await self.session.merge(model)

    async def get_column_info_by_id(self, column_id: str) -> ColumnInfo | None:
        result: ColumnInfoMySQL | None = await self.session.get(ColumnInfoMySQL, column_id)

        if result is None:
            return None

        return ColumnInfoMapper.to_entity(result)

    async def get_table_info_by_id(self, table_id: str) -> TableInfo | None:
        result: TableInfoMySQL | None = await self.session.get(TableInfoMySQL, table_id)

        if result is None:
            return None

        return TableInfoMapper.to_entity(result)

    async def get_key_columns_by_table_id(self, table_id: str) -> list[ColumnInfo]:
        sql = """
            select *
            from column_info
            where table_id = :table_id
              and role in ('primary_key', 'foreign_key')
        """

        result = await self.session.execute(text(sql), {"table_id": table_id})

        return [
            ColumnInfo(**row)
            for row in result.mappings().fetchall()
        ]