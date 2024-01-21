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
            starred: Annotated[bool | None, Query(description="Whether the image is starred.")] = None,
            categories: Annotated[str | None, Query(
                description="The categories whitelist of the image. Image with **any of** the given categories will "
                            "be included. The entries should be seperated by comma.",
                example="stickers, cg")] = None,
            categories_negative: Annotated[
                str | None, Query(
                    description="The categories blacklist of the image. Image with **any of** the given categories "
                                "will be ignored. The entries should be seperated by comma.",
                    example="stickers, cg")] = None,
    ):
        self.preferred_ratio = preferred_ratio
        self.ratio_tolerance = ratio_tolerance
        self.min_width = min_width
        self.min_height = min_height
        self.starred = starred
        # self.categories = categories if categories is not None and len(categories) > 0 else None
        # self.categories_negative = categories_negative if categories_negative is not None and len(
        #     categories_negative) > 0 else None
        bool("fff")
        self.categories = [t for t in categories.split(',') if t] if categories else None
        self.categories_negative = [t for t in categories_negative.split(',') if t] if categories_negative else None
        self.ocr_text = None  # For exact search

    @property
    def min_ratio(self) -> float | None:
        if self.preferred_ratio is None:
            return None
        return self.preferred_ratio * (1 - self.ratio_tolerance)

    @property
    def max_ratio(self) -> float | None:
        if self.preferred_ratio is None:
            return None
        return self.preferred_ratio * (1 + self.ratio_tolerance)
