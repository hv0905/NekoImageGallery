from datetime import datetime
from io import BytesIO
from pathlib import PurePath
from typing import Annotated
from uuid import UUID

from PIL import Image, UnidentifiedImageError
from fastapi import APIRouter, Depends, HTTPException, params, UploadFile, File
from loguru import logger

from app.Models.api_models.admin_api_model import ImageOptUpdateModel, DuplicateValidationModel
from app.Models.api_models.admin_query_params import UploadImageModel
from app.Models.api_response.admin_api_response import ServerInfoResponse, ImageUploadResponse, \
    DuplicateValidationResponse
from app.Models.api_response.base import NekoProtocol
from app.Models.errors import PointDuplicateError
from app.Models.mapped_image import MappedImage
from app.Services.authentication import force_admin_token_verify
from app.Services.provider import ServiceProvider
from app.Services.vector_db_context import PointNotFoundError
from app.config import config
from app.util.generate_uuid import generate_uuid_from_sha1
from app.util.local_file_utility import VALID_IMAGE_EXTENSIONS

admin_router = APIRouter(dependencies=[Depends(force_admin_token_verify)], tags=["Admin"])

services: ServiceProvider | None = None


@admin_router.delete("/delete/{image_id}",
                     description="Delete image with the given id from database. "
                                 "If the image is a local image, it will be moved to `/static/_deleted` folder.")
async def delete_image(
        image_id: Annotated[UUID, params.Path(description="The id of the image you want to delete.")]) -> NekoProtocol:
    try:
        point = await services.db_context.retrieve_by_id(str(image_id))
    except PointNotFoundError as ex:
        raise HTTPException(404, "Cannot find the image with the given ID.") from ex
    await services.db_context.deleteItems([str(point.id)])
    logger.success("Image {} deleted from database.", point.id)

    if config.storage.method.enabled:  # local image
        if point.local:
            image_files = [itm[0] async for itm in
                           services.storage_service.active_storage.list_files("", f"{point.id}.*")]
            assert len(image_files) <= 1
            if not image_files:
                logger.warning("Image {} is a local image but not found in static folder.", point.id)
            else:
                await services.storage_service.active_storage.move(image_files[0], f"_deleted/{image_files[0].name}")
                logger.success("Image {} removed.", image_files[0].name)
        if point.thumbnail_url is not None and (point.local or point.local_thumbnail):
            thumbnail_file = PurePath(f"thumbnails/{point.id}.webp")
            if await services.storage_service.active_storage.is_exist(thumbnail_file):
                await services.storage_service.active_storage.delete(thumbnail_file)
                logger.success("Thumbnail {} removed.", thumbnail_file.name)
            else:
                logger.warning("Thumbnail {} not found.", thumbnail_file.name)

    return NekoProtocol(message="Image deleted.")


@admin_router.put("/update_opt/{image_id}", description="Update a image's optional information")
async def update_image(image_id: Annotated[UUID, params.Path(description="The id of the image you want to delete.")],
                       model: ImageOptUpdateModel) -> NekoProtocol:
    if model.empty():
        raise HTTPException(422, "Nothing to update.")
    try:
        point = await services.db_context.retrieve_by_id(str(image_id))
    except PointNotFoundError as ex:
        raise HTTPException(404, "Cannot find the image with the given ID.") from ex

    if model.thumbnail_url is not None:
        if point.local or point.local_thumbnail:
            raise HTTPException(422, "Cannot change the thumbnail URL of a local image.")
        point.thumbnail_url = model.thumbnail_url
    if model.url is not None:
        if point.local:
            raise HTTPException(422, "Cannot change the URL of a local image.")
        point.url = model.url
    if model.starred is not None:
        point.starred = model.starred
    if model.categories is not None:
        point.categories = model.categories
    if model.comments is not None:
        point.comments = model.comments

    await services.db_context.updatePayload(point)
    logger.success("Image {} updated.", point.id)

    return NekoProtocol(message="Image updated.")


IMAGE_MIMES = {
    "image/jpeg": "jpeg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}


@admin_router.post("/upload",
                   description="Upload image to server. The image will be indexed and stored in the database. If "
                               "local is set to true, the image will be uploaded to local storage.")
async def upload_image(image_file: Annotated[UploadFile, File(description="The image to be uploaded.")],
                       model: Annotated[UploadImageModel, Depends()]) -> ImageUploadResponse:
    # generate an ID for the image
    img_type = None
    if image_file.content_type.lower() in IMAGE_MIMES:
        img_type = IMAGE_MIMES[image_file.content_type.lower()]
    elif image_file.filename:
        extension = PurePath(image_file.filename).suffix.lower()
        if extension in VALID_IMAGE_EXTENSIONS:
            img_type = extension[1:]
    if not img_type:
        logger.warning("Failed to infer image format of the uploaded image. Content Type: {}, Filename: {}",
                       image_file.content_type, image_file.filename)
        raise HTTPException(415, "Unsupported image format.")
    img_bytes = await image_file.read()
    try:
        img_id = await services.upload_service.assign_image_id(img_bytes)
    except PointDuplicateError as ex:
        raise HTTPException(409,
                            f"The uploaded point is already contained in the database! entity id: {ex.entity_id}") \
            from ex
    try:
        image = Image.open(BytesIO(img_bytes))
        image.verify()
        image.close()
    except UnidentifiedImageError as ex:
        logger.warning("Invalid image file from upload request. id: {}", img_id)
        raise HTTPException(422, "Cannot open the image file.") from ex

    mapped_image = MappedImage(id=img_id,
                               url=model.url,
                               thumbnail_url=model.thumbnail_url,
                               local=model.local,
                               categories=model.categories,
                               starred=model.starred,
                               comments=model.comments,
                               format=img_type,
                               index_date=datetime.now())

    await services.upload_service.queue_upload_image(mapped_image, img_bytes, model.skip_ocr, model.local_thumbnail)
    return ImageUploadResponse(message="OK. Image added to upload queue.", image_id=img_id)


@admin_router.get("/server_info", description="Get server information")
async def server_info() -> ServerInfoResponse:
    return ServerInfoResponse(message="Successfully get server information!",
                              image_count=await services.db_context.get_counts(exact=True),
                              index_queue_length=services.upload_service.get_queue_size())


@admin_router.post("/duplication_validate",
                   description="Check if an image exists in the server by its SHA1 hash. If the image exists, "
                               "the image ID will be returned.\n"
                               "This is helpful for checking if an image is already in the server without "
                               "uploading the image.")
async def duplication_validate(model: DuplicateValidationModel) -> DuplicateValidationResponse:
    ids = [generate_uuid_from_sha1(t) for t in model.hashes]
    valid_ids = await services.db_context.validate_ids([str(t) for t in ids])
    exists_matrix = [str(t) in valid_ids or t in services.upload_service.uploading_ids for t in ids]
    return DuplicateValidationResponse(
        exists=exists_matrix,
        entity_ids=[(str(t) if exists else None) for (t, exists) in zip(ids, exists_matrix)],
        message="Validation completed.")
