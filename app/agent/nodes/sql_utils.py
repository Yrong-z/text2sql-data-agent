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
