from fastapi import FastAPI

from app.api.routers.query_router import query_router
from app.core.lifespan import lifespan


app = FastAPI(title="Text-to-SQL Data Agent", version="0.1.0", lifespan=lifespan)
app.include_router(query_router)
