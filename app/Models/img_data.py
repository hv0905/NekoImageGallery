from datetime import datetime
from typing import Optional
from uuid import UUID

from numpy import ndarray
from pydantic import BaseModel, Field


class ImageData(BaseModel):
    id: UUID
    url: str
    thumbnail_url: Optional[str] = None
    ocr_text: Optional[str] = None
    image_vector: Optional[ndarray] = Field(None, exclude=True)
    text_contain_vector: Optional[ndarray] = Field(None, exclude=True)
    index_date: datetime

    @property
    def payload(self):
        return {
            "url": self.url,
            "thumbnail_url": self.thumbnail_url,
            "ocr_text": self.ocr_text,
            "index_date": self.index_date.isoformat()
        }

    @classmethod
    def from_payload(cls, id: str, payload: dict, vector: Optional[ndarray] = None):
        return cls(id=UUID(id),
                   url=payload['url'],
                   thumbnail_url=payload['thumbnail_url'],
                   index_date=datetime.fromisoformat(payload['index_date']),
                   ocr_text=payload['ocr_text'] if 'ocr_text' in payload else None,
                   image_vector=vector)

    class Config:
        arbitrary_types_allowed = True
