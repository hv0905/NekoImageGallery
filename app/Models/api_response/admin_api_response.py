from uuid import UUID

from pydantic import Field

from .base import NekoProtocol


class ServerInfoResponse(NekoProtocol):
    image_count: int
    index_queue_length: int


class DuplicateValidationResponse(NekoProtocol):
    entity_ids: list[UUID | None] = Field(
        description="The image id for each hash. If the image does not exist in the server, the value will be null.")
    exists: list[bool] = Field(
        description="Whether the image exists in the server. True if the image exists, False otherwise.")


class ImageUploadResponse(NekoProtocol):
    image_id: UUID
