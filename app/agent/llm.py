# llm.py
from langchain_deepseek import ChatDeepSeek
from app.conf.app_config import app_config

llm = ChatDeepSeek(
    model=app_config.llm.model_name,
    api_key=app_config.llm.api_key,
    base_url="https://api.deepseek.com",
    temperature=0,
)

if __name__ == "__main__":
    print(llm.invoke("你好").content)