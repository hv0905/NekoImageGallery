from app.Services.storage.local_storage import LocalStorage
from app.Services.storage.s3_compatible_storage import S3Storage
from app.config import config


class StorageService:
    def __init__(self):
        self.local_storage = LocalStorage()
        self.s3_storage = S3Storage()
        self.active_storage = None
        match config.storage.method:
            case "local":
                self.active_storage = self.local_storage
            case "s3":
                self.active_storage = self.s3_storage
            case _:
                raise NotImplementedError(f"Storage method {config.storage.method} not implemented. "
                                          f"Available methods: local, s3")
        self.active_storage.pre_check()
