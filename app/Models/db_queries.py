from typing import Literal, Annotated

from pydantic import BaseModel, Field

from app.Models.api_models.search_api_model import SearchBasisEnum, SearchModelEnum


class DbQueryCriteriaBase(BaseModel):
    type: Literal['id', 'vector']


class DbQueryCriteriaId(DbQueryCriteriaBase):
    type: Literal['id'] = 'id'
    id: str


class DbQueryCriteriaVector(DbQueryCriteriaBase):
    type: Literal['vector'] = 'vector'
    vector: list[float]


DbQueryCriteria = Annotated[DbQueryCriteriaId | DbQueryCriteriaVector, Field(discriminator='type')]


class DbQueryBasis(BaseModel):
    positive: list[DbQueryCriteria] = Field(min_length=1)
    negative: list[DbQueryCriteria] = []
    mix_strategy: SearchModelEnum = SearchModelEnum.average


class DbQuery(BaseModel):
    criteria: dict[SearchBasisEnum, DbQueryBasis] = Field(min_length=1)
