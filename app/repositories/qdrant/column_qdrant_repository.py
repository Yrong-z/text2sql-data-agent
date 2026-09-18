from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct

from app.entities.column_info import ColumnInfo


class ColumnQdrantRepository:

    collection_name = "column_info_collection"

    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    async def ensure_collection(self):

        if not await self.client.collection_exists(self.collection_name):

            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=1024,
                    distance=Distance.COSINE
                ),
            )

    async def upsert(
            self,
            ids: list[str],
            embeddings: list[list[float]],
            payloads: list[dict],
            batch_size: int = 10
    ):

        points = [
            PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )
            for point_id, embedding, payload
            in zip(ids, embeddings, payloads)
        ]

        for i in range(0, len(points), batch_size):

            await self.client.upsert(
                collection_name=self.collection_name,
                points=points[i:i + batch_size]
            )

    async def search(self, embedding:list[float],score_threshold:float=0.6,limit:int=20)->list[ColumnInfo]:
        result = await self.client.query_points(
            collection_name=self.collection_name,
            query=embedding,  # query_vector 改为 query 新版本统一改为了query参数

            limit=limit,
            score_threshold=score_threshold,
        )
        return [ColumnInfo(**point.payload) for point in result.points]