# 部署说明

```powershell
copy .env.example .env
uv sync --no-install-project
docker compose -f docker/docker-compose.yaml up -d
python scripts/init_demo_retrieval.py
```

向量化服务通过 Hugging Face Text Embeddings Inference `cpu-1.8.2` 使用 `BAAI/bge-large-zh-v1.5`。第一次启动时 TEI 会下载模型并保存到挂载在 `/data` 的 Docker 命名卷 `embedding-cache`，需要网络且可能较慢；后续启动会复用缓存。模型文件不会存入 Git 或 Git LFS。`docker compose down` 会保留缓存，`docker compose down -v` 会删除缓存。

MySQL 会自动从 `docker/mysql/` 加载公开虚构 Demo 的表结构和种子数据。检索初始化脚本会根据同一 Demo 数据契约创建 Qdrant 集合和 Elasticsearch 值索引。

公开启动路径不要求主机提供模型目录。
