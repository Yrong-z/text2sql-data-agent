# Deployment

```powershell
copy .env.example .env
uv sync --no-install-project
python scripts/download_embedding_model.py
python scripts/check_embedding_model.py
docker compose -f docker/docker-compose.yaml up -d
python scripts/init_demo_retrieval.py
```

The embedding service uses `BAAI/bge-large-zh-v1.5` through Hugging Face Text
Embeddings Inference `cpu-1.8.2`. The PyTorch weight (`pytorch_model.bin`,
about 1.2 GiB) stays outside Git and Git LFS. The download script validates the
weight size and required tokenizer/config files before reporting success. Set
`EMBEDDING_MODEL_DIR` to a local model directory; the container path remains
`/models/bge-large-zh-v1.5` and the vector size is 1024.

MySQL automatically loads the fictional public demo schema and seed data from
`docker/mysql/`. The retrieval initialization script creates Qdrant collections
and the Elasticsearch value index from the same demo contract.

Docker clean-run was not verified in this environment because Docker Desktop's
Linux engine was unavailable.
