from typing import Optional

from fastapi import Query, HTTPException


class UploadImageModel:
    def __init__(self,
                 url: Optional[str] = Query(None,
                                            description="The image's url. If the image is local, this field will be "
                                                        "ignored. Otherwise it is required."),
                 thumbnail_url: Optional[str] = Query(None,
                                                      description="The image's thumbnail url. If the image is local, "
                                                                  "this field will be ignored."),
                 categories: Optional[str] = Query(None,
                                                   description="The categories of the image. The entries should be "
                                                               "seperated by comma."),
                 starred: bool = Query(False, description="If the image is starred."),
                 local: bool = Query(False,
                                     description="When set to true, the image will be uploaded to local storage. "
                                                 "Otherwise, it will only be indexed in the database."),
                 skip_ocr: bool = Query(False, description="Whether to skip the OCR process.")):
        self.url = url
        self.thumbnail_url = thumbnail_url
        self.categories = [t.strip() for t in categories.split(',') if t.strip()] if categories else None
        self.starred = starred
        self.local = local
        self.skip_ocr = skip_ocr
        if not self.url and not self.local:
            raise HTTPException(422, "A correspond url must be provided for a non-local image.")
