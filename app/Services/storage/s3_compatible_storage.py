# pylint now reporting `opendal` as a `no-name-in-module` error, so we need to disable it as a temporary workaround
# Related issue: https://github.com/pylint-dev/pylint/issues/9185
# Remove below `# pylint` once the issue is resolved
# pylint: disable=import-error,no-name-in-module
import os
import urllib.parse
from pathlib import PurePosixPath
from typing import Optional, AsyncGenerator

import aiofiles
from loguru import logger
from opendal import AsyncOperator
from opendal.exceptions import NotFound, PermissionDenied, AlreadyExists
from wcmatch import glob

from app.Services.storage.base import BaseStorage, FileMetaDataT, RemoteFilePathType, LocalFilePathType, \
    LocalFileMetaDataType, RemoteFileMetaDataType
from app.Services.storage.exception import LocalFileNotFoundError, RemoteFileNotFoundError, RemoteFilePermissionError, \
    RemoteFileExistsError
from app.config import config
from app.util.local_file_utility import VALID_IMAGE_EXTENSIONS


def transform_exception(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except FileNotFoundError as ex:
            raise LocalFileNotFoundError from ex
        except NotFound as ex:
            raise RemoteFileNotFoundError from ex
        except PermissionDenied as ex:
            raise RemoteFilePermissionError from ex
        except AlreadyExists as ex:
            raise RemoteFileExistsError from ex

    return wrapper


class S3Storage(BaseStorage[FileMetaDataT: None]):
    def __init__(self):
        super().__init__()

        # Paths
        self.static_dir = PurePosixPath(config.storage.s3.path)
        self.thumbnails_dir = self.static_dir / "thumbnails"
        self.deleted_dir = self.static_dir / "_deleted"

        self.file_metadata = None
        self.bucket = config.storage.s3.bucket
        self.region = config.storage.s3.region
        self.endpoint = config.storage.s3.endpoint_url

        self.op = AsyncOperator("s3",
                                root=str(self.static_dir),
                                bucket=self.bucket,
                                region=self.region,
                                endpoint=self.endpoint,
                                access_key_id=config.storage.s3.access_key_id,
                                secret_access_key=config.storage.s3.secret_access_key)

        self._file_path_str_warp = lambda x: str(PurePosixPath(x))

    @staticmethod
    def _file_path_str_wrap(p: RemoteFilePathType):
        return str(PurePosixPath(p))

    async def is_exist(self,
                       remote_file: "RemoteFilePathType") -> bool:
        try:
            # the easiest way to confirm the existence of a file
            await self.op.stat(self._file_path_str_warp(remote_file))
            return True
        except NotFound:
            return False

    @transform_exception
    async def size(self,
                   remote_file: "RemoteFilePathType") -> int:
        _stat = await self.op.stat(self._file_path_str_warp(remote_file))
        return _stat.content_length

    @transform_exception
    async def url(self,
                  remote_file: "RemoteFilePathType") -> str:
        return f"{self._res_endpoint}/{str(self.static_dir)}/{str(remote_file)}"

    @transform_exception
    async def presign_url(self,
                          remote_file: "RemoteFilePathType",
                          expire_second: int = 3600) -> str:
        _presign = await self.op.presign_read(self._file_path_str_warp(remote_file), expire_second)
        return _presign.url

    @transform_exception
    async def fetch(self,
                    remote_file: "RemoteFilePathType") -> bytes:
        with await self.op.read(self._file_path_str_warp(remote_file)) as f:
            return bytes(f)

    @transform_exception
    async def upload(self,
                     local_file: "LocalFilePathType",
                     remote_file: "RemoteFilePathType") -> None:
        if isinstance(local_file, bytes):
            b = local_file
        else:
            async with aiofiles.open(local_file, "rb") as f:
                b = await f.read()
        await self.op.write(self._file_path_str_warp(remote_file), b)
        local_file = f"{len(local_file)} bytes" if isinstance(local_file, bytes) else local_file
        logger.success(f"Successfully uploaded file {str(local_file)} to {str(remote_file)} via s3_storage.")

    @transform_exception
    async def copy(self,
                   old_remote_file: "RemoteFilePathType",
                   new_remote_file: "RemoteFilePathType") -> None:
        await self.op.copy(self._file_path_str_warp(old_remote_file), self._file_path_str_warp(new_remote_file))
        logger.success(f"Successfully copied file {str(old_remote_file)} to {str(new_remote_file)} via s3_storage.")

    @transform_exception
    async def move(self,
                   old_remote_file: "RemoteFilePathType",
                   new_remote_file: "RemoteFilePathType") -> None:
        await self.op.copy(self._file_path_str_warp(old_remote_file), self._file_path_str_warp(new_remote_file))
        await self.op.delete(self._file_path_str_warp(old_remote_file))
        logger.success(f"Successfully moved file {str(old_remote_file)} to {str(new_remote_file)} via s3_storage.")

    @transform_exception
    async def delete(self,
                     remote_file: "RemoteFilePathType") -> None:
        await self.op.delete(self._file_path_str_warp(remote_file))
        logger.success(f"Successfully deleted file {str(remote_file)} via s3_storage.")

    async def list_files(self,
                         path: RemoteFilePathType,
                         pattern: Optional[str] = "*",
                         batch_max_files: Optional[int] = None,
                         valid_extensions: Optional[set[str]] = None) \
            -> AsyncGenerator[list[RemoteFilePathType], None]:
        if valid_extensions is None:
            valid_extensions = VALID_IMAGE_EXTENSIONS
        files = []
        # In opendal, current path should be "" instead of "."
        _path = "" if self._file_path_str_warp(path) == "." else self._file_path_str_warp(path)
        async for itm in await self.op.scan(_path):
            if self._list_files_check(itm.path, pattern, valid_extensions):
                files.append(PurePosixPath(itm.path))
                if batch_max_files is not None and len(files) == batch_max_files:
                    yield files
                    files = []
        if files:
            yield files

    async def update_metadata(self,
                              local_file_metadata: "LocalFileMetaDataType",
                              remote_file_metadata: "RemoteFileMetaDataType") -> None:
        raise NotImplementedError

    @staticmethod
    def _list_files_check(x: str, pattern: str, valid_extensions: Optional[set[str]] = None) -> bool:
        matches_pattern = glob.globmatch(x, pattern, flags=glob.GLOBSTAR)
        has_valid_extension = os.path.splitext(x)[-1] in valid_extensions
        is_not_directory = not x.endswith("/")
        return matches_pattern and has_valid_extension and is_not_directory

    @property
    def _res_endpoint(self):
        parsed_url = urllib.parse.urlparse(self.endpoint)
        # If the endpoint is a subdomain of the bucket, then the endpoint is already resolved.
        if self.bucket in parsed_url.netloc.split('.'):
            return self.endpoint
        return f"{self.endpoint}/{self.bucket}"
