from enum import Enum
from fastapi import HTTPException
from pydantic import BaseModel, Field


class SearchCombinedPriorityEnum(str, Enum):
    vision = "vision"
    ocr = "ocr"


class SearchBasisEnum(str, Enum):
    vision = "vision"
    ocr = "ocr"
    combined = "combined"


class SearchModelEnum(str, Enum):
    average = "average"
    best = "best"


class AdvancedSearchModel(BaseModel):
    criteria: list[str] = Field([], description="The positive criteria you want to search with", max_items=16)
    negative_criteria: list[str] = Field([], description="The negative criteria you want to search with", max_items=16)
    mode: SearchModelEnum = Field(SearchModelEnum.average,
                                  description="The mode you want to use to combine the criteria.")
    extra_prompt: str = Field("", description="The image prompt text you want to search.")
    combined_priority: SearchCombinedPriorityEnum = Field(SearchCombinedPriorityEnum.ocr,
                                                          description="The priority of the combined vector.")

    def validate_combined(self, basis: SearchBasisEnum):
        if basis == SearchBasisEnum.combined:
            if not self.extra_prompt:
                raise HTTPException(status_code=422, detail="extra_prompt is required for combined search mode.")
            if 3 > len(self.extra_prompt) > 100:
                raise HTTPException(status_code=422, detail="extra_prompt length should be between 3 and 100.")
