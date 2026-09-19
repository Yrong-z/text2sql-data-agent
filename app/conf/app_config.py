# 日志配置
from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

from omegaconf import OmegaConf

@dataclass
class File:
    enable: bool
    level: str
    path: str
    rotation: str
    retention: str

@dataclass
class Console:
    enable: bool
    level: str

@dataclass
class LoggingConfig:
    file: File
    console: Console

# 数据库配置
@dataclass
class DBConfig:
    host: str
    port: int
    user: str
    password: str
    database: str

@dataclass
class QdrantConfig:
    host: str
    port: int
    embedding_size: int

@dataclass
class EmbeddingConfig:
    host: str
    port: int
    model: str

@dataclass
class ESConfig:
    host: str
    port: int
    index_name: str

@dataclass
class LLMConfig:
    model_name: str
    api_key: str
    base_url: str

@dataclass
class AppConfig:
    logging: LoggingConfig
    db_meta: DBConfig
    db_dw: DBConfig
    qdrant: QdrantConfig
    embedding: EmbeddingConfig
    es: ESConfig
    llm: LLMConfig

load_dotenv(Path(__file__).resolve().parents[3] / ".env")
if os.getenv("PLATFORM_ENV_FILE"):
    load_dotenv(os.getenv("PLATFORM_ENV_FILE"), override=False)

config_file = Path(__file__).parents[2] / 'conf' / 'app_config.yaml'
context = OmegaConf.load(config_file)
schema = OmegaConf.structured(AppConfig)
app_config: AppConfig = OmegaConf.to_object(OmegaConf.merge(schema, context))













# from attr import dataclass
# from omegaconf import OmegaConf
#
# from pathlib import Path
#
# from pydantic.v1.schema import schema
#
#
# @dataclass
# class AppConfig:
#     name:str
#     age:int
#     height:float
#
# config_file =  Path(__file__).parents[2] / 'conf' / 'app_config.yaml'
#
# content = OmegaConf.load(config_file)
#
# schema = OmegaConf.structured(AppConfig)
#
# app_conf: AppConfig =   OmegaConf.to_object(OmegaConf.merge(schema,content))
#
# print(app_conf.name)
# # OmegaConf.merge(schema,content)
#
# # print(conf['name'])
# # print(type(conf))
