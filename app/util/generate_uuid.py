import hashlib
import io
import pathlib
from uuid import UUID, uuid5, NAMESPACE_DNS

NAMESPACE_STR = 'github.com/hv0905/NekoImageGallery'
namespace_uuid = uuid5(NAMESPACE_DNS, NAMESPACE_STR)


def generate(file_input: pathlib.Path | io.BytesIO | bytes) -> UUID:
    if isinstance(file_input, pathlib.Path):
        with open(file_input, 'rb') as f:
            file_content = f.read()
    elif isinstance(file_input, io.BytesIO):
        file_input.seek(0)
        file_content = file_input.read()
    elif isinstance(file_input, bytes):
        file_content = file_input
    else:
        raise ValueError("Unsupported file type. Must be pathlib.Path or io.BytesIO.")
    file_hash = hashlib.sha1(file_content).hexdigest()
    return uuid5(namespace_uuid, file_hash)
