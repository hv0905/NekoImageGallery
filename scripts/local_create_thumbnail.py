import uuid
from pathlib import Path

from PIL import Image
from loguru import logger

from app.Services import db_context
from app.config import config


async def main():
    static_path = Path(config.static_file.path)
    static_thumb_path = static_path / 'thumbnails'
    if not static_thumb_path.exists():
        static_thumb_path.mkdir()
    count = 0
    for item in static_path.glob('*.*'):
        count += 1
        logger.info("[{}] Processing {}", str(count), str(item.relative_to(static_path)))
        size = item.stat().st_size
        if size < 1024 * 500:
            logger.warning("File size too small: {}. Skip...", size)
            continue
        try:
            if item.suffix not in ['.jpg', '.png', '.jpeg']:
                logger.warning("Unsupported file type: {}. Skip...", item.suffix)
                continue
            if (static_thumb_path / f'{item.stem}.webp').exists():
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
            img = Image.open(item)
        except Exception as e:
            logger.error("Error when opening image {}: {}", item, e)
            continue

        # generate thumbnail max size 256*256
        img.thumbnail((256, 256))
        img.save(static_thumb_path / f'{str(image_id)}.webp', 'WebP')
        img.close()
        logger.success("Thumbnail for {} generated!", image_id)

        # update payload
        imgdata.thumbnail_url = f'/static/thumbnails/{str(image_id)}.webp'
        await db_context.updatePayload(imgdata)
        logger.success("Payload for {} updated!", image_id)

    logger.success("OK. Updated {} items.", count)
