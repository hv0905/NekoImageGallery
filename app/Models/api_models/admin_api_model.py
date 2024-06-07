from typing import Optional

from pydantic import BaseModel, Field


class ImageOptUpdateModel(BaseModel):
    starred: Optional[bool] = Field(None,
                                    description="Whether the image is starred or not. Leave empty to keep the value "
                                                "unchanged.")
    categories: Optional[list[str]] = Field(None,
                                            description="The categories of the image. Leave empty to keep the value "
                                                        "unchanged.")
    url: Optional[str] = Field(None,
                               description="The url of the image. Leave empty to keep the value unchanged. Changing "
                                           "the url of a local image is not allowed.")

    thumbnail_url: Optional[str] = Field(None,
                                         description="The url of the thumbnail. Leave empty to keep the value "
                                                     "unchanged. Changing the thumbnail_url of an image with a local "
                                                     "thumbnail is not allowed.")

    def empty(self) -> bool:
        return all([item is None for item in self.model_dump().values()])
