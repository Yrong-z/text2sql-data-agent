import asyncio

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import dw_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.conf.app_config import app_config

router = APIRouter(tags=["health"])


@router.get("/health/live")
async def health_live():
    return {"status": "live", "service": "t2s"}


async def _check(name, operation):
    try:
        await asyncio.wait_for(operation(), timeout=5)
        return name, "ok"
    except Exception as exc:
        return name, f"failed: {type(exc).__name__}"


@router.get("/health/ready")
async def health_ready():
    async def mysql():
        async with dw_mysql_client_manager.session_factory() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))

    async def qdrant():
        await qdrant_client_manager.client.get_collections()

    async def elasticsearch():
        await es_client_manager.client.info()

    async def embedding():
        await embedding_client_manager.client.aembed_query("health")

    checks = dict(await asyncio.gather(
        _check("mysql", mysql),
        _check("qdrant", qdrant),
        _check("elasticsearch", elasticsearch),
        _check("embedding", embedding),
    ))
    checks["llm_config"] = "ok" if app_config.llm.api_key and app_config.llm.base_url else "missing"
    ready = all(name == "llm_config" or value == "ok" for name, value in checks.items())
    payload = {"status": "ready" if ready else "not_ready", "service": "t2s", "checks": checks}
    return JSONResponse(payload, status_code=200 if ready else 503)
