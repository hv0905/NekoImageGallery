import io
from uuid import UUID

from app.util.generate_uuid import generate_uuid
from ..assets import assets_path

BSN_UUID = UUID('b3aff1e9-8085-5300-8e06-37b522384659')  # To test consistency of UUID across versions


def test_uuid_consistency():
    file_path = assets_path / 'test_images' / 'bsn_0.jpg'
    with open(file_path, 'rb') as f:
        file_content = f.read()

    uuid1 = generate_uuid(file_path)
    uuid2 = generate_uuid(io.BytesIO(file_content))
    uuid3 = generate_uuid(file_content)

    assert uuid1 == uuid2 == uuid3 == BSN_UUID
