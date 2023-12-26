from typing import Annotated

from fastapi.params import Query


class SearchPagingParams:
    def __init__(
            self,
            count: Annotated[int, Query(ge=1, le=100, description="The number of results you want to get.")] = 10,
            skip: Annotated[int, Query(ge=0, description="The number of results you want to skip.")] = 0
    ):
        self.count = count
        self.skip = skip


class FilterParams:
    def __init__(
            self,
            preferred_ratio: Annotated[
                float | None, Query(gt=0, description="The preferred aspect ratio of the image.")] = None,
            ratio_tolerance: Annotated[
                float, Query(gt=0, lt=1, description="The tolerance of the aspect ratio.")] = 0.1,
            min_width: Annotated[int | None, Query(geq=0, description="The minimum width of the image.")] = None,
            min_height: Annotated[int | None, Query(geq=0, description="The minimum height of the image.")] = None,
            starred: Annotated[bool | None, Query(description="Whether the image is starred.")] = None):
        self.preferred_ratio = preferred_ratio
        self.ratio_tolerance = ratio_tolerance
        self.min_width = min_width
        self.min_height = min_height
        self.starred = starred
        self.ocr_text = None  # For exact search

        if self.preferred_ratio:
            self.min_ratio = self.preferred_ratio * (1 - self.ratio_tolerance)
            self.max_ratio = self.preferred_ratio * (1 + self.ratio_tolerance)
        else:
            self.min_ratio = None
            self.max_ratio = None
