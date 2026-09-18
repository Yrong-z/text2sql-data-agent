"""Build the smallest public-demo retrieval indexes.

Run after MySQL, Qdrant, Elasticsearch, and TEI are healthy. The payloads
mirror docker/mysql/02_meta_seed.sql and contain fictional values only.
"""
from __future__ import annotations

import asyncio
import os
import uuid

import httpx
from elasticsearch import AsyncElasticsearch
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams


QDRANT_URL = f"http://{os.getenv('QDRANT_HOST', 'localhost')}:{os.getenv('QDRANT_PORT', '6333')}"
ES_URL = f"http://{os.getenv('ELASTICSEARCH_HOST', 'localhost')}:{os.getenv('ELASTICSEARCH_PORT', '9200')}"
EMBEDDING_URL = f"http://{os.getenv('EMBEDDING_HOST', 'localhost')}:{os.getenv('EMBEDDING_PORT', '8081')}"


COLUMNS = [
    ("fact_order.order_amount", "order_amount", "measure", "订单金额 销售额 订单总额", ["199.90", "1797.00"]),
    ("fact_order.order_quantity", "order_quantity", "measure", "订单数量 销量 购买数量 件数", ["1", "3"]),
    ("dim_region.province", "province", "dimension", "省份 地区", ["浙江省", "四川省"]),
    ("dim_region.region_name", "region_name", "dimension", "区域 大区 地区", ["华东", "西南"]),
    ("dim_product.product_name", "product_name", "dimension", "商品名称 产品名称", ["云墨水杯", "星河耳机"]),
    ("dim_product.category", "category", "dimension", "品类 商品类别 分类", ["家居", "数码"]),
    ("dim_date.year", "year", "dimension", "年份 年", ["2025"]),
    ("dim_date.quarter", "quarter", "dimension", "季度", ["Q1"]),
]
METRICS = [
    ("GMV", "GMV 成交总额 销售额 订单总额", ["fact_order.order_amount"]),
    ("AOV", "AOV 平均订单金额 客单价", ["fact_order.order_amount"]),
]
VALUES = [
    ("dim_region.province", "浙江省"), ("dim_region.province", "四川省"),
    ("dim_region.region_name", "华东"), ("dim_region.region_name", "西南"),
    ("dim_product.product_name", "云墨水杯"), ("dim_product.product_name", "星河耳机"),
    ("dim_product.category", "家居"), ("dim_product.category", "数码"),
    ("dim_date.year", "2025"), ("dim_date.quarter", "Q1"),
]


async def embed(texts: list[str]) -> list[list[float]]:
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(f"{EMBEDDING_URL}/embed", json={"inputs": texts})
        response.raise_for_status()
        return response.json()


async def main() -> None:
    vectors = await embed([text for _, _, _, text, _ in COLUMNS] + [text for _, text, _ in METRICS])
    qdrant = AsyncQdrantClient(url=QDRANT_URL)
    try:
        for collection in ("column_info_collection", "metric_info_collection"):
            if not await qdrant.collection_exists(collection):
                await qdrant.create_collection(
                    collection_name=collection,
                    vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE),
                )

        column_points = []
        for index, (column_id, name, role, text, examples) in enumerate(COLUMNS):
            table_id = column_id.rsplit(".", 1)[0]
            column_points.append(PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"column:{column_id}")),
                vector=vectors[index],
                payload={
                    "id": column_id, "name": name, "type": "decimal" if "amount" in name else "varchar",
                    "role": role, "examples": examples, "description": text,
                    "alias": text.split(), "table_id": table_id, "sync": True,
                },
            ))
        metric_offset = len(COLUMNS)
        metric_points = []
        for index, (metric_id, text, relevant_columns) in enumerate(METRICS):
            metric_points.append(PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"metric:{metric_id}")),
                vector=vectors[metric_offset + index],
                payload={"id": metric_id, "name": metric_id, "description": text,
                         "relevant_columns": relevant_columns, "alias": text.split()},
            ))
        await qdrant.upsert(collection_name="column_info_collection", points=column_points)
        await qdrant.upsert(collection_name="metric_info_collection", points=metric_points)
    finally:
        await qdrant.close()

    es = AsyncElasticsearch(ES_URL)
    try:
        if not await es.indices.exists(index="value_index"):
            await es.indices.create(index="value_index", mappings={
                "dynamic": False,
                "properties": {
                    "id": {"type": "keyword"},
                    "value": {"type": "text"},
                    "column_id": {"type": "keyword"},
                },
            })
        operations = []
        for column_id, value in VALUES:
            value_id = f"{column_id}.{value}"
            operations.extend([
                {"index": {"_index": "value_index", "_id": value_id}},
                {"id": value_id, "value": value, "column_id": column_id},
            ])
        if operations:
            await es.bulk(operations=operations)
    finally:
        await es.close()
    print("Demo retrieval indexes initialized.")


if __name__ == "__main__":
    asyncio.run(main())
