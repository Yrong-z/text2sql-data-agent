# Deployment

```powershell
copy .env.example .env
uv sync --no-install-project
docker compose -f docker/docker-compose.yaml up -d
python scripts/init_demo_retrieval.py
```

The embedding service uses `BAAI/bge-large-zh-v1.5` through Hugging Face Text
Embeddings Inference `cpu-1.8.2`. On first startup TEI downloads the model from
Hugging Face and stores it in the named Docker volume `embedding-cache` mounted
at `/data`. The first startup requires internet access and may be slow; later
starts reuse the cache. Model weights are never stored in Git or Git LFS.
`docker compose down` preserves the cache; `docker compose down -v` removes it.

MySQL automatically loads the fictional public demo schema and seed data from
`docker/mysql/`. The retrieval initialization script creates Qdrant collections
and the Elasticsearch value index from the same demo contract.

The public startup path does not require a host model directory.
