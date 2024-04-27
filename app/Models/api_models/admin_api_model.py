from typing import Optional

from pydantic import BaseModel, Field, model_validator


class ImageOptUpdateModel(BaseModel):
    starred: Optional[bool] = Field(None,
                                    description="Whether the image is starred or not. Leave empty to keep the value "
                                                "unchanged.")
    categories: Optional[list[str]] = Field(None,
                                            description="The categories of the image. Leave empty to keep the value "
                                                        "unchanged.")

    def empty(self) -> bool:
        return self.starred is None and self.categories is None


class UploadImageModel(BaseModel):
    url: Optional[str] = Field(None,
                               description="The image's url. If the image is local, this field will be ignored. Otherwise it is required.")
    thumbnail_url: Optional[str] = Field(None,
                                         description="The image's thumbnail url. If the image is local, this field will be ignored.")

    categories: Optional[list[str]] = Field(None, description="The categories of the image.")
    starred: bool = Field(False, description="If the image is starred.")
    local: bool = Field(False,
                        description="When set to true, the image will be uploaded to local storage. Otherwise, it will only be indexed in the database.")
    skip_ocr: bool = Field(False, description="Whether to skip the OCR process.")

    @model_validator(mode='after')
    def validate(self) -> 'UploadImageModel':
        if not self.url and not self.local:
            raise ValueError("A correspond url must be provided for a non-local image.")
        return self
