from datetime import datetime
from typing import Optional
from uuid import UUID

from numpy import ndarray
from pydantic import BaseModel, Field, ConfigDict


class ImageData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='ignore')

    id: UUID
    url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    ocr_text: Optional[str] = None
    image_vector: Optional[ndarray] = Field(None, exclude=True)
    text_contain_vector: Optional[ndarray] = Field(None, exclude=True)
    index_date: datetime
    width: Optional[int] = None
    height: Optional[int] = None
    aspect_ratio: Optional[float] = None
    starred: Optional[bool] = False
    categories: Optional[list[str]] = []
    local: Optional[bool] = False
    local_thumbnail: Optional[bool] = False
    format: Optional[str] = None  # required for s3 local storage

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
