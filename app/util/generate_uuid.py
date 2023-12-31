import io
import pathlib
import hashlib
from uuid import UUID, uuid5, NAMESPACE_DNS

NAMESPACE_STR = 'github.com/hv0905/NekoImageGallery'


def generate(file_input: pathlib.Path | io.BytesIO) -> UUID:
    namespace_uuid = uuid5(NAMESPACE_DNS, NAMESPACE_STR)
    if isinstance(file_input, pathlib.Path):
        with open(file_input, 'rb') as f:
            file_content = f.read()
    elif isinstance(file_input, io.BytesIO):
        file_input.seek(0)
        file_content = file_input.read()
    else:
        raise ValueError("Unsupported file type. Must be pathlib.Path or io.BytesIO.")
    file_hash = hashlib.sha1(file_content).hexdigest()
    return uuid5(namespace_uuid, file_hash)
