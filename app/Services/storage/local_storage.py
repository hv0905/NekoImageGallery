import os
from asyncio import to_thread
from pathlib import Path as syncPath
from shutil import copy2, move
from typing import Optional, AsyncGenerator

import aiofiles
from aiopath import Path as asyncPath
from loguru import logger

from app.Services.storage.base import BaseStorage, FileMetaDataT, RemoteFilePathType, LocalFilePathType
from app.Services.storage.exception import RemoteFileNotFoundError, LocalFileNotFoundError, RemoteFilePermissionError, \
    LocalFilePermissionError, LocalFileExistsError, RemoteFileExistsError
from app.config import config


def transform_exception(param: str):
    file_not_found_exp_map = {"local": LocalFileNotFoundError, "remote": RemoteFileNotFoundError}
    permission_exp_map = {"remote": RemoteFilePermissionError, "local": LocalFilePermissionError}
    file_exist_map = {"local": LocalFileExistsError, "remote": RemoteFileExistsError}

    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except FileNotFoundError as ex:
                raise file_not_found_exp_map[param] from ex
            except PermissionError as ex:
                raise permission_exp_map[param] from ex
            except FileExistsError as ex:
                raise file_exist_map[param] from ex

        return wrapper

    return decorator


class LocalStorage(BaseStorage[FileMetaDataT: None]):
    def __init__(self):
        super().__init__()
        self.static_dir = syncPath(os.path.abspath(config.storage.local.path))
        self.thumbnails_dir = self.static_dir / "thumbnails"
        self.deleted_dir = self.static_dir / "_deleted"
        self.file_metadata = None
        self.file_path_warp = lambda x: self.static_dir / syncPath(x)

    def file_path_wrap(self, path: RemoteFilePathType) -> syncPath:
        return self.static_dir / syncPath(path)

    def pre_check(self):
        if not self.static_dir.is_dir():
            self.static_dir.mkdir(parents=True)
            logger.warning(f"static_dir {self.static_dir} not found, created.")
        if not self.thumbnails_dir.is_dir():
            self.thumbnails_dir.mkdir(parents=True)
            logger.warning(f"thumbnails_dir {self.thumbnails_dir} not found, created.")
        if not self.deleted_dir.is_dir():
            self.deleted_dir.mkdir(parents=True)
            logger.warning(f"deleted_dir {self.deleted_dir} not found, created.")

    async def is_exist(self,
                       remote_file: "RemoteFilePathType") -> bool:
        return self.file_path_warp(remote_file).exists()

    @transform_exception("remote")
    async def size(self,
                   remote_file: "RemoteFilePathType") -> int:
        _file = self.file_path_warp(remote_file)
        return self.file_path_warp(remote_file).stat().st_size

    # noinspection PyMethodMayBeStatic
    async def url(self,
                  remote_file: "RemoteFilePathType") -> str:
        return f"/static/{str(remote_file)}"

    async def presign_url(self,
                          remote_file: "RemoteFilePathType",
                          expire_second: int = 3600) -> str:
        return f"/static/{str(remote_file)}"

    @transform_exception("remote")
    async def fetch(self,
                    remote_file: "RemoteFilePathType") -> bytes:
        remote_file = self.file_path_warp(remote_file)
        async with aiofiles.open(str(remote_file), 'rb') as file:
            return await file.read()

    @transform_exception("local")
    async def upload(self,
                     local_file: "LocalFilePathType",
                     remote_file: "RemoteFilePathType") -> None:
        remote_file = self.file_path_warp(remote_file)
        if isinstance(local_file, bytes):
            async with aiofiles.open(str(remote_file), 'wb') as file:
                await file.write(local_file)
        else:
            await to_thread(copy2, str(local_file), str(remote_file))
        local_file = f"{len(local_file)} bytes" if isinstance(local_file, bytes) else local_file
        logger.success(f"Successfully uploaded file {str(local_file)} to {str(remote_file)} via local_storage.")

    @transform_exception("remote")
    async def copy(self,
                   old_remote_file: "RemoteFilePathType",
                   new_remote_file: "RemoteFilePathType") -> None:
        old_remote_file = self.file_path_warp(old_remote_file)
        new_remote_file = self.file_path_warp(new_remote_file)
        await to_thread(copy2, str(old_remote_file), str(new_remote_file))
        logger.success(f"Successfully copied file {str(old_remote_file)} to {str(new_remote_file)} via local_storage.")

    @transform_exception("remote")
    async def move(self,
                   old_remote_file: "RemoteFilePathType",
                   new_remote_file: "RemoteFilePathType") -> None:
        old_remote_file = self.file_path_warp(old_remote_file)
        new_remote_file = self.file_path_warp(new_remote_file)
        await to_thread(move, str(old_remote_file), str(new_remote_file), copy_function=copy2)
        logger.success(f"Successfully moved file {str(old_remote_file)} to {str(new_remote_file)} via local_storage.")

    @transform_exception("remote")
    async def delete(self,
                     remote_file: "RemoteFilePathType") -> None:
        remote_file = self.file_path_warp(remote_file)
        await to_thread(os.remove, str(remote_file))
        logger.success(f"Successfully deleted file {str(remote_file)} via local_storage.")

    async def list_files(self,
                         path: RemoteFilePathType,
                         pattern: Optional[str] = "*",
                         batch_max_files: Optional[int] = None,
                         valid_extensions: Optional[set[str]] = None) \
            -> AsyncGenerator[list[RemoteFilePathType], None]:
        _path = asyncPath(self.file_path_warp(path))
        files = []
        if valid_extensions is None:
            valid_extensions = {'.jpg', '.png', '.jpeg', '.jfif', '.webp', '.gif'}
        async for file in _path.glob(pattern):
            if file.suffix.lower() in valid_extensions:
                files.append(syncPath(file))
                if batch_max_files is not None and len(files) == batch_max_files:
                    yield files
                    files = []
        if files:
            yield files

    async def update_metadata(self,
                              local_file_metadata: None,
                              remote_file_metadata: None) -> None:
        raise NotImplementedError
