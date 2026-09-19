from typing import TypedDict, Any, Annotated
import operator

from app.entities.column_info import ColumnInfo
from app.entities.metric_info import MetricInfo
from app.entities.value_info import ValueInfo


class ColumnInfoState(TypedDict):
    name: str
    type: str
    role: str
    examples: list[Any]
    description: str
    alias: list[str]


class TableInfoState(TypedDict):
    name: str
    role: str
    description: str
    columns: list[ColumnInfoState]


class MetricInfoState(TypedDict):
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]


class DateInfoState(TypedDict):
    date: str
    weekday: str
    quarter: str


class DBInfoState(TypedDict):
    dialect: str
    version: str


class DataAgentState(TypedDict, total=False):
    query: str
    keywords: list[str]

    # 三个召回节点是并行执行的，所以这里必须使用 reducer 合并结果
    retrieved_columns: Annotated[list[ColumnInfo], operator.add]
    retrieved_values: Annotated[list[ValueInfo], operator.add]
    retrieved_metrics: Annotated[list[MetricInfo], operator.add]

    table_infos: list[TableInfoState]
    metric_infos: list[MetricInfoState]

    date_info: DateInfoState
    db_info: DBInfoState

    sql: str
    error: str | None
    validation_attempts: int
