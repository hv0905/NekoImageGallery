from enum import Enum

from pydantic import BaseModel, Field


class SearchBasisEnum(str, Enum):
    vision = "vision"
    ocr = "ocr"


class SearchModelEnum(str, Enum):
    average = "average"
    best = "best"


class AdvancedSearchModel(BaseModel):
    criteria: list[str] = Field([],
                                description="The positive criteria you want to search with",
                                max_length=16,
                                min_length=1)
    negative_criteria: list[str] = Field([],
                                         description="The negative criteria you want to search with",
                                         max_length=16)
    mode: SearchModelEnum = Field(SearchModelEnum.average,
                                  description="The mode you want to use to combine the criteria.")


class CombinedSearchModel(AdvancedSearchModel):
    extra_prompt: str = Field(max_length=100,
                              description="The secondary prompt used for filtering the image.")


class HybridSearchModel(BaseModel):
    vision: AdvancedSearchModel = Field(description="The vision search criteria.")
    ocr: AdvancedSearchModel = Field(description="The OCR search criteria.")
