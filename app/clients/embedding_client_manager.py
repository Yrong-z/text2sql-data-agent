from app.conf.app_config import EmbeddingConfig, app_config

import asyncio
from typing import List
import httpx
from langchain.embeddings.base import Embeddings


class DockerEmbeddings(Embeddings):
    """
    直接对接本地 Docker TEI 服务的嵌入客户端。
    需要的参数只有 api_url，例如：http://localhost:8081
    """
    def __init__(self, api_url: str):
        self.api_url = api_url.rstrip("/")

    async def _aembed(self, texts: List[str]) -> List[List[float]]:
        """异步核心请求，返回双层列表 [[...], [...]]"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.api_url}/embed",
                json={"inputs": texts},
                timeout=30.0
            )
            resp.raise_for_status()
            return resp.json()  # 你的 Docker 返回的就是 [[...], ...]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """同步批处理接口（LangChain 要求实现）"""
        return asyncio.run(self._aembed(texts))

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """异步批处理接口"""
        return await self._aembed(texts)

    def embed_query(self, text: str) -> List[float]:
        """同步单条查询"""
        return asyncio.run(self._aembed([text]))[0]

    async def aembed_query(self, text: str) -> List[float]:
        """异步单条查询（你的代码里用的就是这个）"""
        embeddings = await self._aembed([text])
        return embeddings[0]


class EmbeddingClientManager:
    def __init__(self, config: EmbeddingConfig):
        self.client: DockerEmbeddings | None = None
        self.config = config

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        self.client = DockerEmbeddings(api_url=self._get_url())

    # def init(self):
    #     self.client = HuggingFaceInferenceAPIEmbeddings(
    #         api_url=self._get_url(),          # 你的本地 Docker 地址
    #         model_name="your-model-id",       # 可以填任意标识，比如 "bge-base-en-v1.5"
    #         # api_key=None                    # 如果需要认证再填写
    #     )




embedding_client_manager = EmbeddingClientManager(app_config.embedding)

if __name__ == "__main__":
    embedding_client_manager.init()
    client = embedding_client_manager.client

    async def test():
        text = "What is deep learning?"
        query_result = await client.aembed_query(text)
        print(query_result[:3])

    asyncio.run(test())


