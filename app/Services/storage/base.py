import abc
import os
from typing import TypeVar, Generic, TypeAlias, Optional, AsyncGenerator

from app.Models.img_data import ImageData

FileMetaDataT = TypeVar('FileMetaDataT')

PathLikeType: TypeAlias = str | os.PathLike
LocalFilePathType: TypeAlias = PathLikeType | bytes
RemoteFilePathType: TypeAlias = PathLikeType
LocalFileMetaDataType: TypeAlias = FileMetaDataT
RemoteFileMetaDataType: TypeAlias = FileMetaDataT


class BaseStorage(abc.ABC, Generic[FileMetaDataT]):
    def __init__(self):
        self.static_dir: os.PathLike
        self.thumbnails_dir: os.PathLike
        self.deleted_dir: os.PathLike
        self.file_metadata: FileMetaDataT

    @abc.abstractmethod
    def pre_check(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def is_exist(self,
                       remote_file: RemoteFilePathType) -> bool:
        """
        Check if a remote_file exists.
        :param remote_file: The file path relative to static_dir
        :return: True if the file exists, False otherwise
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def size(self,
                   remote_file: RemoteFilePathType) -> int:
        """
        Get the size of a file in static_dir
        :param remote_file: The file path relative to static_dir
        :return: file's size
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def url(self,
                  remote_file: RemoteFilePathType) -> str:
        """
        Get the original URL of a file in static_dir.
        This url will be placed in the payload field of the qdrant.
        :param remote_file: The file path relative to static_dir
        :return: file's "original URL"
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def presign_url(self,
                          remote_file: RemoteFilePathType,
                          expire_second: int = 3600) -> str:
        """
        Get the presign URL of a file in static_dir.
        :param remote_file: The file path relative to static_dir
        :param expire_second: Valid time for presign url
        :return: file's "presign URL"
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def fetch(self,
                    remote_file: RemoteFilePathType) -> bytes:
        """
        Fetch a file from static_dir
        :param remote_file: The file path relative to static_dir
        :return: file's content
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def upload(self,
                     local_file: "LocalFilePathType",
                     remote_file: RemoteFilePathType) -> None:
        """
        Move a local picture file to the static_dir.
        :param local_file: The absolute path to the local file or bytes.
        :param remote_file: The file path relative to static_dir
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def copy(self,
                   old_remote_file: RemoteFilePathType,
                   new_remote_file: RemoteFilePathType) -> None:
        """
        Copy a file in static_dir.
        :param old_remote_file: The file path relative to static_dir
        :param new_remote_file: The file path relative to static_dir
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def move(self,
                   old_remote_file: RemoteFilePathType,
                   new_remote_file: RemoteFilePathType) -> None:
        """
        Move a file in static_dir.
        :param old_remote_file: The file path relative to static_dir
        :param new_remote_file: The file path relative to static_dir
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def delete(self,
                     remote_file: RemoteFilePathType) -> None:
        """
        Move a file in static_dir.
        :param remote_file: The file path relative to static_dir
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def list_files(self,
                         path: RemoteFilePathType,
                         pattern: Optional[str] = "*",
                         batch_max_files: Optional[int] = None,
                         valid_extensions: Optional[set[str]] = None) \
            -> AsyncGenerator[list[RemoteFilePathType], None]:
        """
        Asynchronously generates a list of files from a given base directory path that match a specified pattern and set
         of file extensions.

        :param path: The relative base directory path from which relative to static_dir to start listing files.
        :param pattern: A glob pattern to filter files based on their names. Defaults to '*' which selects all files.
        :param batch_max_files: The maximum number of files to return. If None, all matching files are returned.
        :param valid_extensions: An extra set of file extensions to include (e.g., {".jpg", ".png"}).
               If None, files are not filtered by extension.
        :return: An asynchronous generator yielding lists of RemoteFilePathType objects representing the matching files.

        Usage example:
        async for batch in list_files(base_path=".", pattern="*", max_files=100, valid_extensions={".jpg", ".png"}):
            print(f"Batch: {batch}")
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def update_metadata(self,
                              local_file_metadata: LocalFileMetaDataType,
                              remote_file_metadata: RemoteFileMetaDataType) -> None:
        raise NotImplementedError

    async def get_image_url(self, img: ImageData) -> str:
        return img.url

    async def get_image_thumbnails_url(self, img: ImageData) -> str:
        return img.thumbnail_url
