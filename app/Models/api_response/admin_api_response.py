from uuid import UUID

from .base import NekoProtocol


class ServerInfoResponse(NekoProtocol):
    image_count: int


class ImageUploadResponse(NekoProtocol):
    image_id: UUID
