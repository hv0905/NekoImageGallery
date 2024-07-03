from app.Services.lifespan_service import LifespanService
from app.Services.storage.local_storage import LocalStorage
from app.Services.storage.s3_compatible_storage import S3Storage
from app.config import config, StorageMode


class StorageService(LifespanService):
    def __init__(self):
        self.local_storage = LocalStorage()
        self.active_storage = None
        match config.storage.method:
            case StorageMode.LOCAL:
                self.active_storage = self.local_storage
            case StorageMode.S3:
                self.active_storage = S3Storage()
            case StorageMode.DISABLED:
                return
            case _:
                raise NotImplementedError(f"Storage method {config.storage.method} not implemented. "
                                          f"Available methods: local, s3")

    async def on_load(self):
        await self.active_storage.on_load() if self.active_storage else await self.local_storage.on_load()

    async def on_exit(self):
        await self.active_storage.on_exit() if self.active_storage else await self.local_storage.on_exit()

