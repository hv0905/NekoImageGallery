from datetime import datetime
from typing import Optional, Annotated
from uuid import UUID

from numpy import ndarray
from pydantic import BaseModel, Field, ConfigDict


class MappedImage(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='ignore')

    id: Annotated[
        UUID, Field(description="The unique ID of the image. The ID is generated from the digest of the image.")] = None
    url: Annotated[Optional[str], Field(
        description="The URL of the image. For non-local images, this is specified by uploader.")] = None
    thumbnail_url: Annotated[Optional[str], Field(
        description="The URL of the thumbnail image. For non-local thumbnails, "
                    "this is specified by uploader.")] = None
    ocr_text: Annotated[
        Optional[str], Field(description="The OCR text of the image. None if no OCR text was detected.")] = None
    image_vector: Annotated[Optional[ndarray], Field(exclude=True)] = None
    text_contain_vector: Annotated[Optional[ndarray], Field(exclude=True)] = None
    index_date: Annotated[datetime, Field(description="The date when the image was indexed.")]
    width: Annotated[Optional[int], Field(description="The width of the image in pixels.")] = None
    height: Annotated[Optional[int], Field(description="The height of the image in pixels.")] = None
    aspect_ratio: Annotated[Optional[float], Field(
        description="The aspect ratio of the image. calculated by width / height.")] = None
    starred: Annotated[Optional[bool], Field(description="Whether the image is starred.")] = False
    categories: Annotated[Optional[list[str]], Field(description="The categories of the image.")] = []
    local: Annotated[Optional[bool], Field(
        description="Whether the image is stored in local storage.(local image)")] = False
    local_thumbnail: Annotated[Optional[bool], Field(
        description="Whether the thumbnail image is stored in local storage.")] = False
    format: Optional[str] = None  # required for s3 local storage
    comments: Annotated[Optional[str], Field(description="Any custom comments or text payload for the image.")] = None

    @property
    def ocr_text_lower(self) -> str | None:
        if self.ocr_text is None:
            return None
        return self.ocr_text.lower()

    @property
    def payload(self):
        result = self.model_dump(exclude={'id', 'index_date'})
        # Qdrant database cannot accept datetime object, so we have to convert it to string
        result['index_date'] = self.index_date.isoformat()
        # Qdrant doesn't support case-insensitive search, so we need to store a lowercase version of the text
        result['ocr_text_lower'] = self.ocr_text_lower
        return result

    @classmethod
    def from_payload(cls, img_id: str, payload: dict,
                     image_vector: Optional[ndarray] = None, text_contain_vector: Optional[ndarray] = None):
        # Convert the datetime string back to datetime object
        index_date = datetime.fromisoformat(payload['index_date'])
        del payload['index_date']
        return cls(id=UUID(img_id),
                   index_date=index_date,
                   **payload,
                   image_vector=image_vector if image_vector is not None else None,
                   text_contain_vector=text_contain_vector if text_contain_vector is not None else None)
