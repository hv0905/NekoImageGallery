import os
from enum import Enum

from loguru import logger
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

DOCKER_SECRETS_DIR = '/run/secrets'


class QdrantMode(str, Enum):
    SERVER = 'server'
    LOCAL = 'local'
    MEMORY = 'memory'


class QdrantSettings(BaseModel):
    mode: QdrantMode = QdrantMode.SERVER

    host: str = 'localhost'
    port: int = 6333
    grpc_port: int = 6334
    coll: str = 'NekoImg'
    prefer_grpc: bool = True
    api_key: str | None = None

    local_path: str = './images_metadata'


class ModelsSettings(BaseModel):
    clip: str = 'openai/clip-vit-large-patch14'
    bert: str = 'bert-base-chinese'
    easypaddleocr: str | None = None


class OCRSearchSettings(BaseModel):
    enable: bool = True
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
    user_endpoint_url: str | None = None


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
    method: StorageMode = StorageMode.LOCAL
    s3: S3StorageSettings = S3StorageSettings()
    local: LocalStorageSettings = LocalStorageSettings()


# [Deprecated]
class StaticFileSettings(BaseModel):
    path: str = '[DEPRECATED]'
    enable: bool = True  # Deprecated


class Config(BaseSettings):
    qdrant: QdrantSettings = QdrantSettings()
    model: ModelsSettings = ModelsSettings()
    ocr_search: OCRSearchSettings = OCRSearchSettings()
    static_file: StaticFileSettings = StaticFileSettings()  # [Deprecated]
    storage: StorageSettings = StorageSettings()

    device: str = 'auto'
    cors_origins: set[str] = {'*'}
    admin_api_enable: bool = False
    admin_token: str = ''
    admin_index_queue_max_length: int = 200

    access_protected: bool = False
    access_token: str = ''

    model_config = SettingsConfigDict(env_prefix="app_", env_nested_delimiter='__',
                                      env_file=('config/default.env', 'config/local.env'),
                                      env_file_encoding='utf-8',
                                      secrets_dir=DOCKER_SECRETS_DIR if os.path.exists(
                                          DOCKER_SECRETS_DIR) else None)  # for docker secret


class Environment(BaseModel):
    local_indexing: bool = False


def _check_deprecated_settings(_config):
    if _config.static_file.path != '[DEPRECATED]':
        logger.warning("Config StaticFileSettings is deprecated and should not be set.")


config = Config()
environment = Environment()
_check_deprecated_settings(config)
