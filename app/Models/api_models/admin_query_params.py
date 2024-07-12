from enum import Enum
from typing import Optional

from fastapi import Query, HTTPException


class UploadImageThumbnailMode(str, Enum):
    IF_NECESSARY = "if_necessary"
    ALWAYS = "always"
    NEVER = "never"


class UploadImageModel:
    def __init__(self,
                 url: Optional[str] = Query(None,
                                            description="The image's url. If the image is local, this field will be "
                                                        "ignored. Otherwise it is required."),
                 thumbnail_url: Optional[str] = Query(None,
                                                      description="The image's thumbnail url. If the image is local "
                                                                  "or local_thumbnail's value is always, "
                                                                  "this field will be ignored. Currently setting a "
                                                                  "external thumbnail for a local image is "
                                                                  "unsupported due to compatibility issues."),
                 categories: Optional[str] = Query(None,
                                                   description="The categories of the image. The entries should be "
                                                               "seperated by comma."),
                 starred: bool = Query(False, description="If the image is starred."),
                 local: bool = Query(False,
                                     description="When set to true, the image will be uploaded to local storage. "
                                                 "Otherwise, it will only be indexed in the database."),
                 local_thumbnail: UploadImageThumbnailMode =
                 Query(default=None,
                       description="Whether to generate thumbnail locally. Possible values:\n"
                                   "- `if_necessary`: Only generate thumbnail if the image is larger than 500KB. "
                                   "This is the default value if `local=True`\n"
                                   " - `always`: Always generate thumbnail.\n"
                                   " - `never`: Never generate thumbnail. This is the default value if `local=False`."),
                 skip_ocr: bool = Query(False, description="Whether to skip the OCR process."),
                 comments: Optional[str] = Query(None,
                                                 description="Any custom comments or text payload for the image.")):
        self.url = url
        self.thumbnail_url = thumbnail_url
        self.categories = [t.strip() for t in categories.split(',') if t.strip()] if categories else None
        self.starred = starred
        self.local = local
        self.skip_ocr = skip_ocr
        self.comments = comments
        self.local_thumbnail = local_thumbnail if (local_thumbnail is not None) else (
            UploadImageThumbnailMode.IF_NECESSARY if local else UploadImageThumbnailMode.NEVER)
        if not self.url and not self.local:
            raise HTTPException(422, "A correspond url must be provided for a non-local image.")
