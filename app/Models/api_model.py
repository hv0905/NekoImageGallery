from enum import Enum

from pydantic import BaseModel, Field


class SearchModelEnum(str, Enum):
    average = "average"
    best = "best"


class AdvancedSearchModel(BaseModel):
    criteria: list[str] = Field([], description="The positive criteria you want to search with", max_items=16)
    negative_criteria: list[str] = Field([], description="The negative criteria you want to search with", max_items=16)
    mode: SearchModelEnum = Field(SearchModelEnum.average,
                                  description="The mode you want to use to combine the criteria.")
