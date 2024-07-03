from typing import Optional, AsyncGenerator

from app.Services.storage import BaseStorage
from app.Services.storage.base import RemoteFilePathType, LocalFileMetaDataType, RemoteFileMetaDataType, \
    LocalFilePathType


class DisabledStorage(BaseStorage):  # pragma: no cover
    async def size(self, remote_file: RemoteFilePathType) -> int:
        raise NotImplementedError

    async def url(self, remote_file: RemoteFilePathType) -> str:
        raise NotImplementedError

    async def presign_url(self, remote_file: RemoteFilePathType, expire_second: int = 3600) -> str:
        raise NotImplementedError

    async def fetch(self, remote_file: RemoteFilePathType) -> bytes:
        raise NotImplementedError

    async def upload(self, local_file: "LocalFilePathType", remote_file: RemoteFilePathType) -> None:
        raise NotImplementedError

    async def copy(self, old_remote_file: RemoteFilePathType, new_remote_file: RemoteFilePathType) -> None:
        raise NotImplementedError

    async def move(self, old_remote_file: RemoteFilePathType, new_remote_file: RemoteFilePathType) -> None:
        raise NotImplementedError

    async def delete(self, remote_file: RemoteFilePathType) -> None:
        raise NotImplementedError

    async def update_metadata(self, local_file_metadata: LocalFileMetaDataType,
                              remote_file_metadata: RemoteFileMetaDataType) -> None:
        raise NotImplementedError

    async def list_files(self, path: RemoteFilePathType, pattern: Optional[str] = "*",
                         batch_max_files: Optional[int] = None, valid_extensions: Optional[set[str]] = None) -> \
            AsyncGenerator[list[RemoteFilePathType], None]:
        raise NotImplementedError

    async def is_exist(self, remote_file: RemoteFilePathType) -> bool:
        raise NotImplementedError
