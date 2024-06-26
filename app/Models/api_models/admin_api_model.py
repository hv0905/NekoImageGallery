from typing import Optional, Annotated

from pydantic import BaseModel, Field, StringConstraints


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


Sha1HashString = Annotated[
    str, StringConstraints(min_length=40, max_length=40, pattern=r"[0-9a-f]+", to_lower=True, strip_whitespace=True)]


class DuplicateValidationModel(BaseModel):
    hashes: list[Sha1HashString] = Field(description="The SHA1 hash of the image.", min_length=1)
