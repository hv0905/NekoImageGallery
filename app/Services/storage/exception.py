class StorageExtension(Exception):
    pass


class LocalFileNotFoundError(StorageExtension):
    pass


class LocalFileExistsError(StorageExtension):
    pass


class LocalFilePermissionError(StorageExtension):
    pass


class RemoteFileNotFoundError(StorageExtension):
    pass


class RemoteFileExistsError(StorageExtension):
    pass


class RemoteFilePermissionError(StorageExtension):
    pass


class RemoteConnectError(StorageExtension):
    pass
