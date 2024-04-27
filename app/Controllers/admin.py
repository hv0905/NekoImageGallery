from datetime import datetime
from io import BytesIO
from pathlib import PurePath
from typing import Annotated
from uuid import UUID

from PIL import Image, UnidentifiedImageError
from fastapi import APIRouter, Depends, HTTPException, params, BackgroundTasks, UploadFile, File
from loguru import logger

from app.Models.api_models.admin_api_model import ImageOptUpdateModel
from app.Models.api_models.admin_query_params import UploadImageModel
from app.Models.api_response.admin_api_response import ServerInfoResponse, ImageUploadResponse
from app.Models.api_response.base import NekoProtocol
from app.Models.img_data import ImageData
from app.Services.authentication import force_admin_token_verify
from app.Services.provider import db_context, storage_service, index_service
from app.Services.vector_db_context import PointNotFoundError
from app.config import config
from app.util.generate_uuid import generate

admin_router = APIRouter(dependencies=[Depends(force_admin_token_verify)], tags=["Admin"])


@admin_router.delete("/delete/{image_id}",
                     description="Delete image with the given id from database. "
                                 "If the image is a local image, it will be moved to `/static/_deleted` folder.")
async def delete_image(
        image_id: Annotated[UUID, params.Path(description="The id of the image you want to delete.")]) -> NekoProtocol:
    try:
        point = await db_context.retrieve_by_id(str(image_id))
    except PointNotFoundError as ex:
        raise HTTPException(404, "Cannot find the image with the given ID.") from ex
    await db_context.deleteItems([str(point.id)])
    logger.success("Image {} deleted from database.", point.id)

    if point.local and config.storage.method.enabled:  # local image
        image_files = [itm[0] async for itm in storage_service.active_storage.list_files("", f"{point.id}.*")]
        assert len(image_files) <= 1

        if not image_files:
            logger.warning("Image {} is a local image but not found in static folder.", point.id)
        else:
            await storage_service.active_storage.move(image_files[0], f"_deleted/{image_files[0].name}")
            logger.success("Image {} removed.", image_files[0].name)
        if point.thumbnail_url is not None:
            thumbnail_file = PurePath(f"thumbnails/{point.id}.webp")
            if await storage_service.active_storage.is_exist(thumbnail_file):
                await storage_service.active_storage.delete(thumbnail_file)
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
        point = await db_context.retrieve_by_id(str(image_id))
    except PointNotFoundError as ex:
        raise HTTPException(404, "Cannot find the image with the given ID.") from ex

    if model.starred is not None:
        point.starred = model.starred
    if model.categories is not None:
        point.categories = model.categories

    await db_context.updatePayload(point)
    logger.success("Image {} updated.", point.id)

    return NekoProtocol(message="Image updated.")


async def upload_task(img: Image.Image, img_data: ImageData, img_bytes: bytes, skip_ocr: bool):
    logger.info('Start indexing image {}. Local: {}', img_data.id, img_data.local)
    logger.info('Content length is {} bytes.', len(img_bytes))
    file_name = f"{img_data.id}.{img_data.format}"
    thumb_path = f"thumbnails/{img_data.id}.webp"
    if img_data.local:
        img_data.url = await storage_service.active_storage.url(file_name)
        if len(img_bytes) > 1024 * 500:
            img_thumb = img.copy()
            img_data.thumbnail_url = await storage_service.active_storage.url(f"thumbnails/{img_data.id}.webp")

    await index_service.index_image(img, img_data, skip_ocr=skip_ocr)  # The img might be modified after calling this
    logger.success("Image {} indexed.", img_data.id)

    if img_data.local:
        logger.info("Start uploading image {} to local storage.", img_data.id)
        await storage_service.active_storage.upload(img_bytes, file_name)
        logger.success("Image {} uploaded to local storage.", img_data.id)
        if len(img_bytes) > 1024 * 500:
            img_thumb.thumbnail((256, 256))
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, 'WebP')
            await storage_service.active_storage.upload(img_byte_arr.getvalue(), thumb_path)
            logger.success("Thumbnail for {} generated and uploaded!", img_data.id)


IMAGE_MIMES = {
    "image/jpeg": "jpeg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}


@admin_router.post("/upload",
                   description="Upload image to server. The image will be indexed and stored in the database. If local is set to true, the image will be uploaded to local storage.")
async def upload_image(image_file: Annotated[UploadFile, File(description="The image to be uploaded.")],
                       model: Annotated[UploadImageModel, Depends()],
                       background_tasks: BackgroundTasks):
    # generate an ID for the image
    img_type = None
    if image_file.content_type.lower() in IMAGE_MIMES:
        img_type = IMAGE_MIMES[image_file.content_type.lower()]
    elif image_file.filename:
        extension = PurePath(image_file.filename).suffix.lower()
        if extension in {'.jpg', '.png', '.jpeg', '.jfif', '.webp', '.gif'}:
            img_type = extension[1:]
    if not img_type:
        raise HTTPException(415, "Unsupported image format.")
    img_bytes = await image_file.read()
    img_id = generate(img_bytes)
    if len(await db_context.validate_ids([str(img_id)])) != 0:  # check for duplicate points
        raise HTTPException(409, f"The uploaded point is already contained in the database! entity id: {img_id}")

    try:
        image = Image.open(BytesIO(img_bytes))
    except UnidentifiedImageError as ex:
        raise HTTPException(400, "Cannot open the image file.") from ex

    image_data = ImageData(id=img_id,
                           url=model.url,
                           thumbnail_url=model.thumbnail_url,
                           local=model.local,
                           categories=model.categories,
                           starred=model.starred,
                           format=img_type,
                           index_date=datetime.now())

    background_tasks.add_task(upload_task, image, image_data, img_bytes, model.skip_ocr)
    return ImageUploadResponse(message="OK. Image added to upload queue.", image_id=img_id)


@admin_router.get("/server_info", description="Get server information")
async def server_info():
    return ServerInfoResponse(message="Successfully get server information!",
                              image_count=await db_context.get_counts(exact=True))
