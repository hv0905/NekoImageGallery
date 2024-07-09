from enum import Enum

from pydantic import Field

from app.Models.api_response.base import NekoProtocol
from app.Models.img_data import ImageData


class ImageStatus(str, Enum):
    MAPPED = "mapped"
    IN_QUEUE = "in_queue"


class QueryByIdApiResponse(NekoProtocol):
    img_status: ImageStatus = Field(description="The status of the image.\n"
                                                "Warning: If NekoImageGallery is deployed in a cluster, "
                                                "the `in_queue` might not be accurate since the index queue "
                                                "is independent of each service instance.")
    img: ImageData | None = Field(description="The mapped image data. Only available when `img_status = mapped`.")


class QueryImagesApiResponse(NekoProtocol):
    images: list[ImageData] = Field(description="The list of images.")
    next_page_offset: str = Field(description="The offset ID for the next page query.")
