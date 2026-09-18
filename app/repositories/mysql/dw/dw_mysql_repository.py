from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class DWMySQLRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_column_types(self, table_name: str) -> dict[str, str]:
        sql = f"show columns from {table_name}"
        result = await self.session.execute(text(sql))
        return {row.Field: row.Type for row in result.fetchall()}

    async def get_column_values(self, table_name: str, column_name: str, limit: int):
        sql = f"select distinct {column_name} from {table_name} limit {limit}"
        result = await self.session.execute(text(sql))
        return result.scalars().fetchall()

    async def get_db_info(self):
        """
        获取当前数据仓库数据库信息。

        返回示例：
        {
            "version": "8.0.36",
            "dialect": "mysql"
        }
        """
        result = await self.session.execute(text("select version()"))
        version = result.scalar()

        dialect = self.session.get_bind().dialect.name

        return {
            "version": version,
            "dialect": dialect,
        }


    async def validate_sql(self, sql: str):
        await self.session.execute(text(f"explain {sql}"))

    async def execute_sql(self, sql: str) -> list[dict]:
        """
        执行最终生成的 SQL，并返回 list[dict] 格式结果。
        """
        result = await self.session.execute(text(sql))
        return [dict(row) for row in result.mappings().fetchall()]