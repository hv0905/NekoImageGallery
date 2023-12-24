from enum import Enum
from fastapi import HTTPException
from pydantic import BaseModel, Field


class SearchBasisEnum(str, Enum):
    vision = "vision"
    ocr = "ocr"


class SearchModelEnum(str, Enum):
    average = "average"
    best = "best"


class SearchCombinedBasisEnum(str, Enum):
    vision = "vision"
    ocr = "ocr"


class AdvancedSearchModel(BaseModel):
    criteria: list[str] = Field([], description="The positive criteria you want to search with", max_items=16)
    negative_criteria: list[str] = Field([], description="The negative criteria you want to search with", max_items=16)
    mode: SearchModelEnum = Field(SearchModelEnum.average,
                                  description="The mode you want to use to combine the criteria.")


class CombinedSearchModel(AdvancedSearchModel):
    extra_prompt: str = Field(min_length=3, max_length=100,
                              description="The secondary prompt used for filtering the image.")
