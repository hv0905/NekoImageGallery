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
    device: str = 'auto'
    model: str = 'openai/clip-vit-large-patch14'


class StaticFileSettings(BaseModel):
    path: str = './static'
    enable: bool = True


class Config(BaseSettings):
    qdrant: QdrantSettings = QdrantSettings()
    clip: ClipSettings = ClipSettings()
    static_file: StaticFileSettings = StaticFileSettings()

    cors_origins: set[str] = {'*'}
    admin_api_enable: bool = False
    admin_token: str = ''

    model_config = SettingsConfigDict(env_prefix="app_", env_nested_delimiter='__',
                                      env_file=('config/default.env', 'config/local.env'),
                                      env_file_encoding='utf-8')


config = Config()

print(config.model_dump())
