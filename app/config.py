from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class QdrantSettings(BaseModel):
    host: str = 'localhost'
    port: int = 6333
    grpc_port: int = 6334
    coll: str = ''
    prefer_grpc: bool = False
    api_key: str | None = None


class ClipSettings(BaseModel):
    model: str = 'openai/clip-vit-large-patch14'


class OCRSearchSettings(BaseModel):
    enable: bool = True
    bert_model: str = 'bert-base-chinese'
    ocr_language: list[str] = ['ch_sim', 'en']


class StaticFileSettings(BaseModel):
    path: str = './static'
    enable: bool = True


class Config(BaseSettings):
    qdrant: QdrantSettings = QdrantSettings()
    clip: ClipSettings = ClipSettings()
    ocr_search: OCRSearchSettings = OCRSearchSettings()
    static_file: StaticFileSettings = StaticFileSettings()

    device: str = 'auto'
    cors_origins: set[str] = {'*'}
    admin_api_enable: bool = False
    admin_token: str = ''

    access_protected: bool = False
    access_token: str = 'default-access-token'

    model_config = SettingsConfigDict(env_prefix="app_", env_nested_delimiter='__',
                                      env_file=('config/default.env', 'config/local.env'),
                                      env_file_encoding='utf-8')


class Environment(BaseModel):
    local_indexing: bool = False


config = Config()
environment = Environment()
