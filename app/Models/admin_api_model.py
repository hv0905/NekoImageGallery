from typing import Optional

from pydantic import BaseModel, Field


class ImageOptUpdateModel(BaseModel):
    starred: Optional[bool] = Field(None,
                                    description="Whether the image is starred or not. Leave empty to keep the value "
                                                "unchanged.")
