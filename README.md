# T2S 数据问数服务

这是一个基于 FastAPI、LangGraph、MySQL、Qdrant、Elasticsearch 和本地向量化服务的 T2S 数据问数服务。

## 项目概览

公开版本提供一个小型虚构仓库和元数据模型，用于演示自然语言数据查询。

## 架构

FastAPI → LangGraph T2S 流程 → MySQL 元数据/数据、Qdrant 语义召回、Elasticsearch 值召回和 TEI 向量化。

## 核心流程

`extract keywords → recall columns/values/metrics → merge → filter → context → generate SQL → validate/correct → execute`

## 技术栈

Python、FastAPI、LangGraph、MySQL 8、Qdrant、Elasticsearch、Hugging Face TEI 和 OpenAI 兼容 LLM。

## 本地准备

1. Clone the repository and copy `.env.example` to `.env`.
2. Install the Python dependencies with `uv sync --no-install-project` (the checked-in `uv.lock` pins the environment).
3. Start the local services with `docker compose -f docker/docker-compose.yaml up -d`. TEI downloads `BAAI/bge-large-zh-v1.5` from Hugging Face on first startup and caches it in the Docker `embedding-cache` volume.
5. The MySQL container automatically creates the `meta` and `dw` databases and loads the fictional demo schema and rows from `docker/mysql/`.
6. After TEI and the other services are healthy, initialize the Qdrant and Elasticsearch demo indexes:
   `python scripts/init_demo_retrieval.py`
7. Run the available tests or call `POST /api/query` after the services are healthy.

## 演示问题

The seed data is fictional and intentionally small. These queries exercise the
minimum aggregate, dimension filter, and metric/time/region paths:

1. `统计所有地区的销售总额`
2. `统计浙江省的销售总额`
3. `统计2025年华东地区的订单数量`

## API

`POST /api/query` 接收 `{ "query": "..." }`，返回包含进度、生成 SQL 和执行结果事件的 SSE 流。

查询接口返回 SSE 流。标准运行顺序为：

```text
clean clone → docker compose up -d → MySQL schema/seed → init_demo_retrieval.py → POST /api/query
```

The model weights, `.env`, databases, logs and local virtual environments are intentionally excluded from the repository. The Compose file uses a relative model directory by default and supports `EMBEDDING_MODEL_DIR` for an external local mount.

## 配置

复制 `.env.example` 为 `.env`，并配置 `LLM_MODEL`、`LLM_API_KEY` 和 `LLM_BASE_URL`。数据库和服务地址也通过同一环境文件配置。

## 测试

安装依赖后运行项目测试。Docker 完整清洁启动需要本机环境配合验证。

## 项目结构

```text
app/       API, LangGraph agent, repositories, and clients
conf/      application and metadata configuration
docker/    Compose, MySQL demo schema, Elasticsearch, and embedding service
scripts/   model and retrieval initialization utilities
docs/      embedding deployment note
```

## 当前限制

- 完整 Docker 启动需要 Docker Desktop 和外部 LLM 配置。
- Demo 只使用虚构种子数据。
- SQL 生成和修正依赖配置的 LLM 服务。
