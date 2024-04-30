from enum import Enum

from loguru import logger
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class QdrantSettings(BaseModel):
    host: str = 'localhost'
    port: int = 6333
    grpc_port: int = 6334
    coll: str = 'NekoImg'
    prefer_grpc: bool = True
    api_key: str | None = None


class ClipSettings(BaseModel):
    model: str = 'openai/clip-vit-large-patch14'


class OCRSearchSettings(BaseModel):
    enable: bool = True
    bert_model: str = 'bert-base-chinese'
    ocr_module: str = 'easypaddleocr'
    ocr_language: list[str] = ['ch_sim', 'en']
    ocr_min_confidence: float = 1e-2


class S3StorageSettings(BaseModel):
    path: str = "./static"
    bucket: str | None = None
    region: str | None = None
    endpoint_url: str | None = None
    access_key_id: str | None = None
    secret_access_key: str | None = None
    session_token: str | None = None


class LocalStorageSettings(BaseModel):
    path: str = './static'


class StorageMode(str, Enum):
    LOCAL = 'local'
    S3 = 's3'
    DISABLED = 'disabled'

    @property
    def enabled(self):
        return self != StorageMode.DISABLED


class StorageSettings(BaseModel):
    method: StorageMode = StorageMode.DISABLED  # set designed to be "disabled" for compatibility checking in StaticFileSettings
    s3: S3StorageSettings = S3StorageSettings()
    local: LocalStorageSettings = LocalStorageSettings()


# [Deprecated]
class StaticFileSettings(BaseModel):
    path: str = '[DEPRECATED]'
    enable: bool = True  # Deprecated


class Config(BaseSettings):
    qdrant: QdrantSettings = QdrantSettings()
    clip: ClipSettings = ClipSettings()
    ocr_search: OCRSearchSettings = OCRSearchSettings()
    static_file: StaticFileSettings = StaticFileSettings()  # [Deprecated]
    storage: StorageSettings = StorageSettings()

    device: str = 'auto'
    cors_origins: set[str] = {'*'}
    admin_api_enable: bool = False
    admin_token: str = ''

    access_protected: bool = False
    access_token: str = 'default-access-token'

    model_config = SettingsConfigDict(env_prefix="app_", env_nested_delimiter='__',
                                      env_file=('config/default.env', 'config/local.env'),
                                      env_file_encoding='utf-8',
                                      secrets_dir='/run/secrets')  # for docker secret


class Environment(BaseModel):
    local_indexing: bool = False


def _check_deprecated_settings(_config):
    if _config.static_file.path != '[DEPRECATED]':
        logger.warning("Config StaticFileSettings is deprecated and should not be set.")
    # if _config.storage.method == '[DISABLED]':
    #     raise DeprecationWarning("Config StaticFileSettings is deprecated, use StorageSettings instead!")


config = Config()
environment = Environment()
_check_deprecated_settings(config)
