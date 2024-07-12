from enum import Enum

from pydantic import Field

from app.Models.api_response.base import NekoProtocol
from app.Models.mapped_image import MappedImage


class ImageStatus(str, Enum):
    MAPPED = "mapped"
    IN_QUEUE = "in_queue"


class QueryByIdApiResponse(NekoProtocol):
    img_status: ImageStatus = Field(description="The status of the image.\n"
                                                "Warning: If NekoImageGallery is deployed in a cluster, "
                                                "the `in_queue` might not be accurate since the index queue "
                                                "is independent of each service instance.")
    img: MappedImage | None = Field(description="The mapped image data. Only available when `img_status = mapped`.")


class QueryImagesApiResponse(NekoProtocol):
    images: list[MappedImage] = Field(description="The list of images.")
    next_page_offset: str | None = Field(description="The offset ID for the next page query. "
                                                     "If there are no more images, this field will be null.")
