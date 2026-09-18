# app/api/schemas/query_schema.py

from pydantic import BaseModel


class QuerySchema(BaseModel):
    query: str