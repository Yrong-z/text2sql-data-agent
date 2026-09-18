import uuid
from dataclasses import asdict
from pathlib import Path
from typing import List, Dict, Any

from langchain_huggingface import HuggingFaceEndpointEmbeddings
from omegaconf import OmegaConf

from app.core.log import logger
from app.conf.meta_config import MetaConfig
from app.entities.column_info import ColumnInfo
from app.entities.column_metric import ColumnMetric
from app.entities.metric_info import MetricInfo
from app.entities.value_info import ValueInfo
from app.entities.table_info import TableInfo
from app.repositories.es.value_es_repository import ValueEsRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class MetaKnowledgeService:
    """元知识同步服务，负责将表、字段、指标元数据同步到各类存储中。"""

    def __init__(
        self,
        meta_mysql_repository: MetaMysqlRepository,
        dw_mysql_repository: DWMySQLRepository,
        column_qdrant_repository: ColumnQdrantRepository,
        value_es_repository: ValueEsRepository,
        embedding_client: HuggingFaceEndpointEmbeddings = None,
        metric_qdrant_repository: MetricQdrantRepository = None,
    ):
        self.meta_mysql_repository = meta_mysql_repository
        self.dw_mysql_repository = dw_mysql_repository
        self.column_qdrant_repository = column_qdrant_repository
        self.value_es_repository = value_es_repository
        self.embedding_client = embedding_client
        self.metric_qdrant_repository = metric_qdrant_repository

    # ------------------------------------------------------------------
    # 公共主流程
    # ------------------------------------------------------------------
    async def build(self, config_path: Path) -> None:
        """根据配置文件执行完整的元数据同步。"""
        app_config = self._load_config(config_path)
        logger.info("加载配置文件成功")

        if app_config.tables:
            await self._sync_tables_and_columns(app_config)
        if app_config.metrics:
            await self._sync_metrics(app_config)

    # ------------------------------------------------------------------
    # 配置加载
    # ------------------------------------------------------------------
    def _load_config(self, config_path: Path) -> MetaConfig:
        """加载并解析 OmegaConf 配置文件，返回 MetaConfig 对象。"""
        context = OmegaConf.load(config_path)
        schema = OmegaConf.structured(MetaConfig)
        return OmegaConf.to_object(OmegaConf.merge(schema, context))

    # ------------------------------------------------------------------
    # 表与字段同步
    # ------------------------------------------------------------------
    async def _sync_tables_and_columns(self, app_config: MetaConfig) -> None:
        """同步表、字段元数据到 MySQL，并为字段建立向量和全文索引。"""
        table_infos, column_infos = await self._build_table_column_entities(app_config)

        # 1. 保存到 MySQL
        async with self.meta_mysql_repository.session.begin():
            await self.meta_mysql_repository.save_table_infos(table_infos)
            await self.meta_mysql_repository.save_column_infos(column_infos)
        logger.info("保存表信息和字段信息到数据库成功")

        # 2. 建立向量索引
        points = self._build_column_vector_points(column_infos)
        await self._batch_upsert_vectors(points, self.column_qdrant_repository)
        logger.info("为字段信息建立向量索引成功")

        # 3. 建立字段值全文索引
        await self._sync_column_values(app_config)

    async def _build_table_column_entities(self, app_config: MetaConfig):
        """从配置和数据仓库构建 TableInfo 和 ColumnInfo 实体列表。"""
        table_infos: List[TableInfo] = []
        column_infos: List[ColumnInfo] = []

        for table in app_config.tables:
            table_info = TableInfo(
                id=table.name,
                name=table.name,
                role=table.role,
                description=table.description,
            )
            table_infos.append(table_info)

            column_types = await self.dw_mysql_repository.get_column_types(table.name)
            for column in table.columns:
                column_values = await self.dw_mysql_repository.get_column_values(
                    table.name, column.name, limit=10
                )
                column_info = ColumnInfo(
                    id=f"{table.name}.{column.name}",
                    name=column.name,
                    type=column_types.get(column.name),
                    role=column.role,
                    examples=list(column_values) if column_values else None,
                    description=column.description,
                    alias=column.alias if hasattr(column, "alias") else [],
                    table_id=table.name,
                )
                column_infos.append(column_info)

        return table_infos, column_infos

    def _build_column_vector_points(self, column_infos: List[ColumnInfo]) -> List[Dict[str, Any]]:
        """为字段信息生成待向量化的 points 列表。每个字段生成名称、描述及别名的点。"""
        points = []
        for col in column_infos:
            payload = asdict(col)
            points.append({"id": uuid.uuid4(), "embedding_text": col.name, "payload": payload})
            points.append({"id": uuid.uuid4(), "embedding_text": col.description, "payload": payload})
            for alias in col.alias:
                points.append({"id": uuid.uuid4(), "embedding_text": alias, "payload": payload})
        return points

    async def _sync_column_values(self, app_config: MetaConfig) -> None:
        """同步需要建立全文索引的字段取值到 Elasticsearch。"""
        await self.value_es_repository.ensure_index()
        value_infos: List[ValueInfo] = []

        for table in app_config.tables:
            for column in table.columns:
                if column.sync:
                    current_values = await self.dw_mysql_repository.get_column_values(
                        table.name, column.name, limit=100000
                    )
                    value_infos.extend(
                        ValueInfo(
                            id=f"{table.name}.{column.name}.{v}",
                            value=v,
                            column_id=f"{table.name}.{column.name}",
                        )
                        for v in current_values
                    )

        if value_infos:
            await self.value_es_repository.index(value_infos)

    # ------------------------------------------------------------------
    # 指标同步
    # ------------------------------------------------------------------
    async def _sync_metrics(self, app_config: MetaConfig) -> None:
        """同步指标元数据到 MySQL，并建立向量索引。"""
        metric_infos, column_metrics = self._build_metric_entities(app_config)

        # 1. 保存到 MySQL
        async with self.meta_mysql_repository.session.begin():
            await self.meta_mysql_repository.save_metric_info(metric_infos)
            await self.meta_mysql_repository.save_column_metrics(column_metrics)
        logger.info("保存指标信息到数据库成功")

        # 2. 建立向量索引
        points = self._build_metric_vector_points(metric_infos)
        await self._batch_upsert_vectors(points, self.metric_qdrant_repository)
        logger.info("为指标信息建立向量索引成功")

    def _build_metric_entities(self, app_config: MetaConfig):
        """从配置构建 MetricInfo 和 ColumnMetric 实体列表。"""
        metric_infos: List[MetricInfo] = []
        column_metrics: List[ColumnMetric] = []

        for metric in app_config.metrics:
            metric_info = MetricInfo(
                id=metric.name,
                name=metric.name,
                description=metric.description,
                relevant_columns=metric.relevant_columns,
                alias=metric.alias,
            )
            metric_infos.append(metric_info)

            for col_id in metric.relevant_columns:
                column_metrics.append(ColumnMetric(column_id=col_id, metric_id=metric.name))

        return metric_infos, column_metrics

    def _build_metric_vector_points(self, metric_infos: List[MetricInfo]) -> List[Dict[str, Any]]:
        """为指标信息生成待向量化的 points 列表。"""
        points = []
        for m in metric_infos:
            payload = asdict(m)
            points.append({"id": uuid.uuid4(), "embedding_text": m.name, "payload": payload})
            points.append({"id": uuid.uuid4(), "embedding_text": m.description, "payload": payload})
            for alias in m.alias:
                points.append({"id": uuid.uuid4(), "embedding_text": alias, "payload": payload})
        return points

    # ------------------------------------------------------------------
    # 通用向量化与存储
    # ------------------------------------------------------------------
    async def _batch_upsert_vectors(self, points: List[dict], qdrant_repository) -> None:
        """
        对 points 中的文本进行批量向量化，然后存入指定的 Qdrant 仓库。
        points 格式: [{'id': uuid, 'embedding_text': str, 'payload': dict}, ...]
        """
        # 确保 Qdrant 集合存在
        await qdrant_repository.ensure_collection()

        embedding_texts = [p["embedding_text"] for p in points]
        embeddings = []
        batch_size = 20
        for i in range(0, len(embedding_texts), batch_size):
            batch = embedding_texts[i : i + batch_size]
            batch_embeddings = await self.embedding_client.aembed_documents(batch)
            embeddings.extend(batch_embeddings)

        ids = [p["id"] for p in points]
        payloads = [p["payload"] for p in points]
        await qdrant_repository.upsert(ids, embeddings, payloads)
# import uuid
# from dataclasses import asdict
# from pathlib import Path
#
# from langchain_huggingface import HuggingFaceEndpointEmbeddings
# from omegaconf import OmegaConf
#
#
# from app.conf.meta_config import MetaConfig
#
# from app.entities.column_info import ColumnInfo
# from app.entities.column_metric import ColumnMetric
# from app.entities.metric_info import MetricInfo
# from app.entities.value_info import ValueInfo
# from app.entities.table_info import TableInfo
# from app.repositories.es.value_es_repository import ValueEsRepository
# from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
# from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository
#
# from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
# from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
#
#
# class MetaKnowledgeService:
#     def __init__(
#         self,
#         meta_mysql_repository: MetaMysqlRepository,
#         dw_mysql_repository: DWMySQLRepository,
#         column_qdrant_repository: ColumnQdrantRepository,
#         value_es_repository: ValueEsRepository,
#         embedding_client=HuggingFaceEndpointEmbeddings,
#         metric_qdrant_repository=MetricQdrantRepository,
#     ):
#         self.meta_mysql_repository = meta_mysql_repository
#         self.dw_mysql_repository = dw_mysql_repository
#         self.column_qdrant_repository = column_qdrant_repository
#         self.value_es_repository = value_es_repository
#         self.embedding_client = embedding_client
#         self.metric_qdrant_repository:MetricQdrantRepository = metric_qdrant_repository
#
#
#
#     async def build(self, config_path: Path):
#         context = OmegaConf.load(config_path)
#         schema = OmegaConf.structured(MetaConfig)
#         app_config: MetaConfig = OmegaConf.to_object(OmegaConf.merge(schema, context))
#
#
#         if app_config.tables:
#             table_infos: list[TableInfo] = [] #不再使用存储层，定义业务实体类
#             column_infos: list[ColumnInfo] = [] #存储层实体类
#
#             for table in app_config.tables:
#                 table_info = TableInfo(
#                     id=table.name,
#                     name=table.name,
#                     role=table.role,
#                     description=table.description
#                 )
#                 table_infos.append(table_info)
#
#                 column_types = await self.dw_mysql_repository.get_column_types(table.name)
#
#                 for column in table.columns:
#                     column_values = await self.dw_mysql_repository.get_column_values(
#                          table.name, column.name, limit=10  # limit 可按需调整
#                     )
#                     column_info = ColumnInfo(
#                         id=f"{table.name}.{column.name}",
#                         name=column.name,
#                         type=column_types.get(column.name),
#                         role=column.role,
#                         examples=list(column_values) if column_values else None,
#                         description=column.description,
#                         alias=column.alias if hasattr(column, "alias") else [],
#                         table_id=table.name
#                     )
#                     column_infos.append(column_info)
#
#             async with self.meta_mysql_repository.session.begin():  #生命周期 回滚
#                 await self.meta_mysql_repository.save_table_infos(table_infos)
#                 await self.meta_mysql_repository.save_column_infos(column_infos)
#                 # await self.meta_mysql_repository.session.commit()
#
#
#             #2.2 对字段信息建立向量索引
#             await self.column_qdrant_repository.ensure_collection()
#             points:list[dict] = []
#             for column_info in column_infos:
#                 points.append({
#                     'id': uuid.uuid4(),
#                     'embedding_text': column_info.name,
#                     'payload': asdict(column_info)
#                 })
#
#                 points.append({
#                     'id': uuid.uuid4(),
#                     'embedding_text': column_info.description,
#                     'payload': asdict(column_info)
#                 })
#
#                 for alia in column_info.alias:
#                     points.append({
#                         'id': uuid.uuid4(),
#                         'embedding_text': alia,
#                         'payload': asdict(column_info)
#                     })
#
#
#             #向量化
#             embeddings:list[list[float]] = []
#             embedding_texts = [point['embedding_text'] for point in points]
#             embedding_batch_size = 20
#             for i in range(0, len(embedding_texts), embedding_batch_size):
#                 batch_embedding_texts = embedding_texts[i:i + embedding_batch_size]
#                 batch_embeddings = await self.embedding_client.aembed_documents(batch_embedding_texts)
#                 embeddings.extend(batch_embeddings)
#
#
#             ids = [point['id'] for point in points]
#
#             payloads = [point['payload'] for point in points]
#
#             await self.column_qdrant_repository.upsert(ids,embeddings,payloads)
#
#
#
#             #2.3 对指定维度字段取值建立全文索引 对字段取值进行检索和匹配
#
#             # 2.3 对指定维度字段取值建立全文索引
#             await self.value_es_repository.ensure_index()
#             value_infos: list[ValueInfo] = []
#
#             for table in (app_config.tables or []):
#                 for column in table.columns:
#                     if column.sync:
#                         current_column_values = await self.dw_mysql_repository.get_column_values(
#                             table.name, column.name, limit=100000
#                         )
#                         current_value_infos = [
#                             ValueInfo(
#                                 id=f"{table.name}.{column.name}.{v}",
#                                 value=v,
#                                 column_id=f"{table.name}.{column.name}"
#                             )
#                             for v in current_column_values
#                         ]
#                         value_infos.extend(current_value_infos)
#
#             await self.value_es_repository.index(value_infos)
#
#
#         #3 根据配置文件同步指定的图标信息
#         if app_config.metrics:
#             #3.1 将指标信息保存在meta数据库中
#             metric_infos: list[MetricInfo] = []
#             column_metrics: list[ColumnMetric] = []
#
#             for metric in app_config.metrics:
#                 metric_info = MetricInfo(
#                     id = metric.name,
#                     name = metric.name,
#                     description = metric.description,
#                     relevant_columns=metric.relevant_columns,
#                     alias=metric.alias,
#                 )
#                 metric_infos.append(metric_info)
#
#                 for column in  metric.relevant_columns:
#                     column_metric = ColumnMetric(
#                         column_id = column,
#                         metric_id = metric.name
#                     )
#                     column_metrics.append(column_metric)
#         async def _save_metric_to_meta_db(self,meta_config: MetaConfig) -> list[MetricInfo]:
#                 self.meta_mysql_repository.save_metric_info(metric_infos)
#                 self.meta_mysql_repository.save_column_metrics(column_metrics)
#             #3.2 对指标信息建立向量索引
#                 await self.metric_qdrant_repository.ensure_collection()
#                 points: list[dict] = []
#                 for metric_info in metric_infos:
#                     points.append({
#                         'id': uuid.uuid4(),
#                         'embedding_text': metric_info.name,
#                         'payload': asdict(metric_info)
#                     })
#
#                     points.append({
#                         'id': uuid.uuid4(),
#                         'embedding_text': metric_info.description,
#                         'payload': asdict(metric_info)
#                     })
#
#                     for alia in metric_info.alias:
#                         points.append({
#                             'id': uuid.uuid4(),
#                             'embedding_text': alia,
#                             'payload': asdict(metric_info)
#                         })
#
#                 # 向量化
#                 embeddings: list[list[float]] = []
#                 embedding_texts = [point['embedding_text'] for point in points]
#                 embedding_batch_size = 20
#                 for i in range(0, len(embedding_texts), embedding_batch_size):
#                     batch_embedding_texts = embedding_texts[i:i + embedding_batch_size]
#                     batch_embeddings = await self.embedding_client.aembed_documents(batch_embedding_texts)
#                     embeddings.extend(batch_embeddings)
#
#                 ids = [point['id'] for point in points]
#
#                 payloads = [point['payload'] for point in points]
#
#                 await self.metric_qdrant_repository.upsert(ids, embeddings, payloads)
#
#
#
#
#
