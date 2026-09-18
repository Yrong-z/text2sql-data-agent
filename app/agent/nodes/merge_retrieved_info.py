from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import (
    ColumnInfoState,
    DataAgentState,
    MetricInfoState,
    TableInfoState,
)
from app.core.log import logger
from app.entities.column_info import ColumnInfo
from app.entities.table_info import TableInfo


async def merge_retrieved_info(
    state: DataAgentState,
    runtime: Runtime[DataAgentContext],
):
    writer = runtime.stream_writer
    step = "合并召回信息"

    writer({"type": "progress", "step": step, "status": "running"})

    try:
        retrieved_columns = state.get("retrieved_columns", [])
        retrieved_metrics = state.get("retrieved_metrics", [])
        retrieved_values = state.get("retrieved_values", [])

        logger.info(f"merge输入 retrieved_columns: {[c.id for c in retrieved_columns]}")
        logger.info(f"merge输入 retrieved_metrics: {[m.id for m in retrieved_metrics]}")
        logger.info(f"merge输入 retrieved_values: {[v.id for v in retrieved_values]}")

        meta_mysql_repository = runtime.context["meta_mysql_repository"]

        retrieved_columns_map: dict[str, ColumnInfo] = {
            column.id: column for column in retrieved_columns
        }

        for metric in retrieved_metrics:
            for column_id in metric.relevant_columns:
                if column_id not in retrieved_columns_map:
                    column_info = await meta_mysql_repository.get_column_info_by_id(
                        column_id
                    )
                    if column_info is not None:
                        retrieved_columns_map[column_id] = column_info

        for value_info in retrieved_values:
            column_id = value_info.column_id
            column_value = value_info.value

            if column_id not in retrieved_columns_map:
                column_info = await meta_mysql_repository.get_column_info_by_id(
                    column_id
                )
                if column_info is not None:
                    retrieved_columns_map[column_id] = column_info

            if column_id in retrieved_columns_map:
                examples = retrieved_columns_map[column_id].examples

                if examples is None:
                    retrieved_columns_map[column_id].examples = [column_value]
                elif column_value not in examples:
                    examples.append(column_value)

        table_to_columns_map: dict[str, list[ColumnInfo]] = {}

        for column_info in retrieved_columns_map.values():
            table_id = column_info.table_id

            if table_id not in table_to_columns_map:
                table_to_columns_map[table_id] = []

            table_to_columns_map[table_id].append(column_info)

        for table_id, columns in table_to_columns_map.items():
            key_columns = await meta_mysql_repository.get_key_columns_by_table_id(
                table_id
            )

            existing_column_ids = {column.id for column in columns}

            for key_column in key_columns:
                if key_column.id not in existing_column_ids:
                    columns.append(key_column)
                    existing_column_ids.add(key_column.id)

        table_infos: list[TableInfoState] = []

        for table_id, columns in table_to_columns_map.items():
            table: TableInfo | None = await meta_mysql_repository.get_table_info_by_id(
                table_id
            )

            if table is None:
                continue

            column_states: list[ColumnInfoState] = [
                ColumnInfoState(
                    name=column.name,
                    type=column.type,
                    role=column.role,
                    examples=column.examples or [],
                    description=column.description,
                    alias=column.alias or [],
                )
                for column in columns
            ]

            table_infos.append(
                TableInfoState(
                    name=table.name,
                    role=table.role,
                    description=table.description,
                    columns=column_states,
                )
            )

        metric_infos: list[MetricInfoState] = [
            MetricInfoState(
                name=metric.name,
                description=metric.description,
                relevant_columns=metric.relevant_columns,
                alias=metric.alias or [],
            )
            for metric in retrieved_metrics
        ]

        writer({"type": "progress", "step": step, "status": "success"})
        logger.info(
            f"合并召回信息成功: 表信息={[table['name'] for table in table_infos]}, "
            f"指标信息={[metric['name'] for metric in metric_infos]}"
        )

        return {
            "table_infos": table_infos,
            "metric_infos": metric_infos,
        }

    except Exception as e:
        writer({"type": "progress", "step": step, "status": "error"})
        logger.exception(f"合并召回信息失败: {e}")
        raise
