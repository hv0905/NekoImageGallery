from typing import Optional

from pydantic import BaseModel, Field


class ImageOptUpdateModel(BaseModel):
    starred: Optional[bool] = Field(None,
                                    description="Whether the image is starred or not. Leave empty to keep the value "
                                                "unchanged.")
    categories: Optional[list[str]] = Field(None,
                                            description="The categories of the image. Leave empty to keep the value "
                                                        "unchanged.")

    def empty(self) -> bool:
        return self.starred is None and self.categories is None
