from pydantic import BaseModel
from .img_data import ImageData


class SearchResult(BaseModel):
    img: ImageData
    score: float
