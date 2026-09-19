from fastapi import FastAPI

from app.api.routers.query_router import query_router
from app.core.lifespan import lifespan
from app.api.routers.health_router import router as health_router


app = FastAPI(title="Text-to-SQL Data Agent", version="0.1.0", lifespan=lifespan)
app.include_router(query_router)
app.include_router(health_router)
