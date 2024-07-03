from app.Services.lifespan_service import LifespanService
from app.Services.storage.base import BaseStorage
from app.Services.storage.disabled_storage import DisabledStorage
from app.Services.storage.local_storage import LocalStorage
from app.Services.storage.s3_compatible_storage import S3Storage
from app.config import config, StorageMode


class StorageService(LifespanService):
    def __init__(self):
        self.active_storage = None
        match config.storage.method:
            case StorageMode.LOCAL:
                self.active_storage = LocalStorage()
            case StorageMode.S3:
                self.active_storage = S3Storage()
            case StorageMode.DISABLED:
                self.active_storage = DisabledStorage()
            case _:
                raise NotImplementedError(f"Storage method {config.storage.method} not implemented. "
                                          f"Available methods: local, s3")

    async def on_load(self):
        await self.active_storage.on_load()

    async def on_exit(self):
        await self.active_storage.on_exit()
