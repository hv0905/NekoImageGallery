from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, HTTPException, Query

from app.Models.api_response.images_api_response import QueryByIdApiResponse, ImageStatus, QueryImagesApiResponse
from app.Models.query_params import FilterParams
from app.Services.authentication import force_access_token_verify
from app.Services.provider import ServiceProvider
from app.Services.vector_db_context import PointNotFoundError
from app.config import config

images_router = APIRouter(dependencies=([Depends(force_access_token_verify)] if config.access_protected else None),
                          tags=["Images"])

services: ServiceProvider | None = None  # The service provider will be injected in the webapp initialize


@images_router.get("/id/{image_id}", description="Query the image info with the given image ID. \n"
                                                 "This can also be used to check the status"
                                                 " of an image in the index queue.")
async def query_image_by_id(image_id: Annotated[UUID, Path(description="The id of the image you want to query.")]):
    try:
        return QueryByIdApiResponse(img=await services.db_context.retrieve_by_id(str(image_id)),
                                    img_status=ImageStatus.MAPPED,
                                    message="Success query the image with the given ID.")
    except PointNotFoundError as ex:
        if services.upload_service and image_id in services.upload_service.uploading_ids:
            return QueryByIdApiResponse(img=None,
                                        img_status=ImageStatus.IN_QUEUE,
                                        message="The image is in the indexing queue.")
        raise HTTPException(404, "Cannot find the image with the given ID.") from ex


@images_router.get("/", description="Query images in order of ID.")
async def scroll_images(filter_param: Annotated[FilterParams, Depends()],
                        prev_offset_id: Annotated[UUID, Query(description="The previous offset image ID.")] = None,
                        count: Annotated[int, Query(ge=1, le=100, description="The number of images to query.")] = 15):
    # validate the offset ID
    if prev_offset_id is not None and len(await services.db_context.validate_ids([str(prev_offset_id)])) == 0:
        raise HTTPException(404, "The previous offset ID is invalid.")
    images, offset = await services.db_context.scroll_points(str(prev_offset_id), count, filter_param=filter_param)
    return QueryImagesApiResponse(images=images, next_page_offset=offset, message="Success query images.")
