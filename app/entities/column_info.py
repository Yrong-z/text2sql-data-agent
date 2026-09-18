from dataclasses import dataclass
from typing import Any

@dataclass
class ColumnInfo:
    id: str
    name: str
    type: str
    role: str
    examples: list[Any] | None = None
    description: str | None = None
    alias: list[str] | None = None
    table_id: str | None = None
    sync: bool = True          # 是否同步到全文索引，默认 True