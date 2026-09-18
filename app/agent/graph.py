# app/agent/graph.py

from langgraph.constants import START, END
from langgraph.graph import StateGraph

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState

# 注意：这里按你项目里的目录名 nodes 来写
# 如果你的真实目录是 nodes，就把下面所有 nodes 改成 nodes
from app.agent.nodes.extract_keywords import extract_keywords
from app.agent.nodes.recall_column import recall_column
from app.agent.nodes.recall_value import recall_value
from app.agent.nodes.recall_metric import recall_metric
from app.agent.nodes.merge_retrieved_info import merge_retrieved_info
from app.agent.nodes.filter_table import filter_table
from app.agent.nodes.filter_metric import filter_metric
from app.agent.nodes.add_extra_context import add_extra_context
from app.agent.nodes.generate_sql import generate_sql
from app.agent.nodes.validate_sql import validate_sql
from app.agent.nodes.correct_sql import correct_sql
from app.agent.nodes.run_sql import run_sql


def route_after_validate_sql(state: DataAgentState) -> str:
    """
    validate_sql 节点会返回：
    - {"error": None}：说明 SQL 校验通过，可以执行 SQL
    - {"error": "..."}：说明 SQL 有问题，进入 correct_sql 修正
    """
    if state.get("error") is None:
        return "run_sql"
    return "correct_sql"


graph_builder = StateGraph(
    state_schema=DataAgentState,
    context_schema=DataAgentContext,
)

# =========================
# 1. 添加节点
# =========================

graph_builder.add_node("extract_keywords", extract_keywords)

graph_builder.add_node("recall_column", recall_column)
graph_builder.add_node("recall_value", recall_value)
graph_builder.add_node("recall_metric", recall_metric)

graph_builder.add_node("merge_retrieved_info", merge_retrieved_info)

graph_builder.add_node("filter_table", filter_table)
graph_builder.add_node("filter_metric", filter_metric)

graph_builder.add_node("add_extra_context", add_extra_context)

graph_builder.add_node("generate_sql", generate_sql)
graph_builder.add_node("validate_sql", validate_sql)
graph_builder.add_node("correct_sql", correct_sql)

graph_builder.add_node("run_sql", run_sql)

# =========================
# 2. 添加边
# =========================

graph_builder.add_edge(START, "extract_keywords")

# 抽取关键词后，三路并行召回
graph_builder.add_edge("extract_keywords", "recall_column")
graph_builder.add_edge("extract_keywords", "recall_value")
graph_builder.add_edge("extract_keywords", "recall_metric")

# 三路召回完成后，汇总召回信息
graph_builder.add_edge("recall_column", "merge_retrieved_info")
graph_builder.add_edge("recall_value", "merge_retrieved_info")
graph_builder.add_edge("recall_metric", "merge_retrieved_info")

# 合并后，并行过滤表和指标
graph_builder.add_edge("merge_retrieved_info", "filter_table")
graph_builder.add_edge("merge_retrieved_info", "filter_metric")

# 表和指标都过滤完，再补充额外上下文
graph_builder.add_edge("filter_table", "add_extra_context")
graph_builder.add_edge("filter_metric", "add_extra_context")

# 生成 SQL
graph_builder.add_edge("add_extra_context", "generate_sql")

# 校验 SQL
graph_builder.add_edge("generate_sql", "validate_sql")

# 校验通过：执行 SQL
# 校验失败：修正 SQL
graph_builder.add_conditional_edges(
    "validate_sql",
    route_after_validate_sql,
    {
        "run_sql": "run_sql",
        "correct_sql": "correct_sql",
    },
)

# 修正后再次执行
# 注意：课程代码是 correct_sql -> execute_sql
# 你当前阶段为了避免死循环，先保持这个版本
graph_builder.add_edge("correct_sql", "run_sql")

# 执行完结束
graph_builder.add_edge("run_sql", END)

graph = graph_builder.compile()