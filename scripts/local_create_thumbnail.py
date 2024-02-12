import io
import uuid

from PIL import Image
from loguru import logger

from app.Services.provider import db_context, storage_service


async def main():
    # Here path maybe either local path or pure path
    count = 0
    async for item in storage_service.active_storage.list_files("", '*.*', batch_max_files=1):
        item = item[0]
        count += 1
        logger.info("[{}] Processing {}", str(count), str(item))
        size = await storage_service.active_storage.size(item)
        if size < 1024 * 500:
            logger.warning("File size too small: {}. Skip...", size)
            continue
        try:
            if await storage_service.active_storage.is_exist(f'thumbnails/{item.stem}.webp'):
                logger.warning("Thumbnail for {} already exists. Skip...", item.stem)
                continue
            image_id = uuid.UUID(item.stem)
        except ValueError:
            logger.warning("Invalid file name: {}. Skip...", item.stem)
            continue
        try:
            imgdata = await db_context.retrieve_by_id(str(image_id))
        except Exception as e:
            logger.error("Error when retrieving image {}: {}", image_id, e)
            continue
        try:
            img_byte = await storage_service.active_storage.fetch(item)
            img = Image.open(io.BytesIO(img_byte))
        except Exception as e:
            logger.error("Error when opening image {}: {}", item, e)
            continue

        # generate thumbnail max size 256*256
        img.thumbnail((256, 256))
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, 'WebP')
        await storage_service.active_storage.upload(img_byte_arr.getvalue(), f'thumbnails/{str(image_id)}.webp')
        logger.success("Thumbnail for {} generated!", image_id)

        # update payload
        imgdata.thumbnail_url = await storage_service.active_storage.url(f'thumbnails/{str(image_id)}.webp')
        await db_context.updatePayload(imgdata)
        logger.success("Payload for {} updated!", image_id)

    logger.success("OK. Updated {} items.", count)
