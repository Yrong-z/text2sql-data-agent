from contextvars import ContextVar

# 每个请求独立保存自己的 request_id
request_id_ctx_var = ContextVar("request_id", default="-")