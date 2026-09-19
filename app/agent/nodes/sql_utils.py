import re


def clean_sql(sql: str) -> str:
    if not isinstance(sql, str):
        raise TypeError("sql must be a string")

    cleaned_sql = sql.strip()

    if not cleaned_sql:
        return cleaned_sql

    cleaned_sql = re.sub(
        r"^```(?:sql)?\s*",
        "",
        cleaned_sql,
        flags=re.IGNORECASE,
    )
    cleaned_sql = re.sub(r"\s*```$", "", cleaned_sql)

    return cleaned_sql.strip()
from sqlglot import exp, parse_one

MAX_RESULT_ROWS = 500


def validate_read_only_select(sql: str) -> str:
    """Parse exactly one MySQL SELECT and return a bounded canonical SQL."""
    if not sql or not sql.strip():
        raise ValueError("SQL为空，无法执行")
    try:
        expression = parse_one(sql, read="mysql")
    except Exception as exc:
        raise ValueError(f"SQL解析失败: {exc}") from exc
    if expression is None or not isinstance(expression, exp.Select):
        raise ValueError("只允许执行单条 SELECT 查询")
    if expression.find(exp.Delete, exp.Insert, exp.Update, exp.Drop, exp.Alter, exp.TruncateTable):
        raise ValueError("SQL包含被禁止的写入或结构变更操作")
    if expression.args.get("limit") is None:
        expression = expression.limit(MAX_RESULT_ROWS)
    return expression.sql(dialect="mysql")
