from typing import Optional

from pydantic import BaseModel
from numpy import ndarray
from datetime import datetime
from uuid import UUID


class ImageData(BaseModel):
    id: UUID
    url: str
    thumbnail_url: Optional[str] = None
    image_vector: Optional[ndarray] = None
    index_date: datetime

    @property
    def payload(self):
        return {
            "url": self.url,
            "thumbnail_url": self.thumbnail_url,
            "index_date": self.index_date.isoformat()
        }

    def from_payload(self, payload: dict):
        self.url = payload["url"]
        self.thumbnail_url = payload["thumbnail_url"]
        self.index_date = datetime.fromisoformat(payload["index_date"])
        return self

    class Config:
        arbitrary_types_allowed = True
