from pydantic import BaseModel

from .mapped_image import MappedImage


class SearchResult(BaseModel):
    img: MappedImage
    score: float
