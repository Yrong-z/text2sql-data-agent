import asyncio
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    async_sessionmaker,
    AsyncSession,
)
from app.conf.app_config import DBConfig, app_config

class MySQLClientManager:
    def __init__(self, config: DBConfig):
        self.engine: AsyncEngine | None = None
        self.session_factory = None        # 可以先声明
        self.config = config

    def _get_url(self):
        return (
            f"mysql+asyncmy://{self.config.user}:{self.config.password}"
            f"@{self.config.host}:{self.config.port}/{self.config.database}?charset=utf8mb4"
        )

    def init(self):
        self.engine = create_async_engine(
            self._get_url(),
            pool_size=10,
            pool_pre_ping=True,
        )
        # ↓↓↓ 添加这一行 ↓↓↓
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,    # 根据需要调整
            autoflush=True,
        )

    async def close(self):
        if self.engine:
            await self.engine.dispose()

meta_mysql_client_manager = MySQLClientManager(app_config.db_meta)
dw_mysql_client_manager = MySQLClientManager(app_config.db_dw)


if __name__ == "__main__":
    dw_mysql_client_manager.init()
    # engine = dw_mysql_client_manager.engine

    async def test():
        # 使用引擎创建一个异步 session 工厂
        async_session = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
        )
        # 调用工厂获得一个 AsyncSession，并用 async with 管理
        async with async_session() as session:
            sql = "select * from fact_order limit 10"
            result = await session.execute(text(sql))
            rows = result.fetchall()

            print(type(rows))
            print(rows)

    asyncio.run(test())


# from pdb import run
#
# from app.conf.app_config import DBConfig, app_config
#
# from redis.commands.search import result
# from sqlalchemy import text
# from sqlalchemy.ext import asyncio
# from sqlalchemy.ext.asyncio import create_async_engine
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker
#
#
#
#
# class MySQLClientManager:
#     def __init__(self,config:DBConfig):
#         self.engine:AsyncEngine | None = None
#         self.config = config
#
#     def _get_url(self):
#         return f"mysql+asyncmy://{self.config.user}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}?charset=utf8mb4"
#
#     def init(self):
#         self.engine = create_async_engine(self._get_url())
#
#
#     async def close(self):
#         await self.engine.dispose()
#
#
# meta_mysql_client_manager = MySQLClientManager(app_config.db_meta)
# dw_mysql_client_manager = MySQLClientManager(app_config.db_dw)
#
# if __name__ == "__main__":
#     dw_mysql_client_manager.init()
#     engine = dw_mysql_client_manager.engine
#
#
#     async def test():
#         async with AsyncSession(engine) as session:
#             sql = "select * from fact_order limit 10"
#
#             result = await session.execute(text(sql))
#
#             result.fetchall()
#
#             print(type(rows))
#             print(rows)
#
#     asyncio,run(test())

