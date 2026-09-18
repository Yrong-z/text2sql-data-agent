# app/agent/nodes/extract_keywords.py

import jieba.analyse
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def extract_keywords(
    state: DataAgentState,
    runtime: Runtime[DataAgentContext],
):
    """
    抽取用户问题中的关键词。

    作用：
    1. 从用户自然语言问题中抽取核心词；
    2. 将原始 query 也放入 keywords，避免分词丢失完整语义；
    3. 通过 runtime.stream_writer 输出节点进度；
    4. 出现异常时输出 error 进度，并继续向上抛出异常，
       让 QueryService 统一转换成 SSE error 消息。
    """

    writer = runtime.stream_writer
    step = "抽取关键词"

    writer({"type": "progress", "step": step, "status": "running"})

    try:
        query = state.get("query")

        if query is None:
            raise ValueError("缺少查询参数 query")

        if not isinstance(query, str):
            raise TypeError("查询参数 query 必须是字符串")

        query = query.strip()

        if not query:
            raise ValueError("查询内容不能为空")

        allow_pos = (
            "n",      # 名词
            "nr",     # 人名
            "ns",     # 地名
            "nt",     # 机构团体名
            "nz",     # 其他专有名词
            "v",      # 动词
            "vn",     # 名动词
            "a",      # 形容词
            "an",     # 名形词
            "eng",    # 英文
            "i",      # 成语
            "l",      # 常用固定短语
        )

        # jieba.analyse.extract_tags 本身支持 allowPOS，
        # 不需要先 pseg.cut 再手动拼接。
        extracted_keywords = jieba.analyse.extract_tags(
            sentence=query,
            topK=20,
            withWeight=False,
            allowPOS=allow_pos,
        )

        # 保留原始 query，防止短句、业务词、组合词被 jieba 拆散后丢失语义
        keywords = [
            keyword.strip()
            for keyword in extracted_keywords + [query]
            if isinstance(keyword, str) and keyword.strip()
        ]

        keywords = [
            keyword.strip()
            for keyword in extracted_keywords + [query]
            if isinstance(keyword, str) and keyword.strip()
        ]

        keywords = list(dict.fromkeys(keywords))

        writer({"type": "progress", "step": step, "status": "success"})

        logger.info(f"抽取关键词: {keywords}")

        return {
            "query": query,
            "keywords": keywords
        }

    except Exception as e:
        writer({"type": "progress", "step": step, "status": "error"})
        logger.exception(f"抽取关键词失败: {e}")

        # 不要在节点里吞掉异常。
        # 继续 raise，让 app/services/query_service.py 捕获，
        # 然后统一返回 SSE error。
        raise