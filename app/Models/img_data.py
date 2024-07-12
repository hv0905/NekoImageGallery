from datetime import datetime
from typing import Optional
from uuid import UUID

from numpy import ndarray
from pydantic import BaseModel, Field, ConfigDict


class ImageData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='ignore')

    id: UUID = Field(description="The unique ID of the image. The ID is generated from the digest of the image.")
    url: Optional[str] = Field(default=None,
                               description="The URL of the image. For non-local images, this is specified by uploader.")
    thumbnail_url: Optional[str] = Field(default=None,
                                         description="The URL of the thumbnail image. For non-local thumbnails, "
                                                     "this is specified by uploader.")
    ocr_text: Optional[str] = Field(default=None,
                                    description="The OCR text of the image. None if no OCR text was detected.")
    image_vector: Optional[ndarray] = Field(None, exclude=True)
    text_contain_vector: Optional[ndarray] = Field(None, exclude=True)
    index_date: datetime = Field(description="The date when the image was indexed.")
    width: Optional[int] = Field(default=None, description="The width of the image in pixels.")
    height: Optional[int] = Field(default=None, description="The height of the image in pixels.")
    aspect_ratio: Optional[float] = Field(default=None,
                                          description="The aspect ratio of the image. calculated by width / height.")
    starred: Optional[bool] = Field(default=False, description="Whether the image is starred.")
    categories: Optional[list[str]] = Field(default=[], description="The categories of the image.")
    local: Optional[bool] = Field(default=False,
                                  description="Whether the image is stored in local storage.(local image).")
    local_thumbnail: Optional[bool] = Field(default=False,
                                            description="Whether the thumbnail image is stored in local storage.")
    format: Optional[str] = None  # required for s3 local storage
    comments: Optional[str] = Field(default=None, description="Any custom comments or text payload for the image.")

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
