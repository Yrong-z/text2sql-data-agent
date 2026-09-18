# Wshu

Wshu is a Text-to-SQL service built around FastAPI, LangGraph, MySQL, Qdrant, Elasticsearch and a local embedding service.

## Project Overview

The public release demonstrates a small fictional warehouse and metadata model.

## Architecture

FastAPI → LangGraph Text-to-SQL pipeline → MySQL metadata/data, Qdrant semantic
recall, Elasticsearch value recall, and TEI embeddings.

## Core Flow

`extract keywords → recall columns/values/metrics → merge → filter → context → generate SQL → validate/correct → execute`

## Tech Stack

Python, FastAPI, LangGraph, MySQL 8, Qdrant, Elasticsearch, Hugging Face TEI,
and an OpenAI-compatible LLM.

## Local setup

1. Clone the repository and copy `.env.example` to `.env`.
2. Install the Python dependencies with `uv sync --no-install-project` (the checked-in `uv.lock` pins the environment).
3. Download and validate `BAAI/bge-large-zh-v1.5` outside Git with `python scripts/download_embedding_model.py` (the Compose TEI image is pinned to `cpu-1.8.2`).
4. Start the local services with `docker compose -f docker/docker-compose.yaml up -d`.
5. The MySQL container automatically creates the `meta` and `dw` databases and loads the fictional demo schema and rows from `docker/mysql/`.
6. After the services are healthy, initialize the Qdrant and Elasticsearch demo indexes:
   `python scripts/init_demo_retrieval.py`
7. Run the available tests or call `POST /api/query` after the services are healthy.

## Public demo queries

The seed data is fictional and intentionally small. These queries exercise the
minimum aggregate, dimension filter, and metric/time/region paths:

1. `统计所有地区的销售总额`
2. `统计浙江省的销售总额`
3. `统计2025年华东地区的订单数量`

## API

`POST /api/query` accepts `{ "query": "..." }` and returns an SSE stream with
progress, generated SQL, and execution result events.

The query endpoint returns an SSE stream. The normal clean run is:

```text
clean clone → docker compose up -d → MySQL schema/seed → init_demo_retrieval.py → POST /api/query
```

The model weights, `.env`, databases, logs and local virtual environments are intentionally excluded from the repository. The Compose file uses a relative model directory by default and supports `EMBEDDING_MODEL_DIR` for an external local mount.

## Configuration

Copy `.env.example` to `.env`. Set `LLM_MODEL`, `LLM_API_KEY`, and `LLM_BASE_URL`
for the provider. Database and service endpoints are configurable through the
same environment file.

## Tests

Run the repository tests after dependencies are installed. Docker clean-run has
not been verified in this environment.

## Project Structure

```text
app/       API, LangGraph agent, repositories, and clients
conf/      application and metadata configuration
docker/    Compose, MySQL demo schema, Elasticsearch, and embedding service
scripts/   model and retrieval initialization utilities
docs/      embedding deployment note
```

## Current Limitations

- The clean Docker run requires Docker Desktop and external LLM configuration.
- The demo uses fictional seed data only.
- SQL generation and correction remain provider-dependent.
