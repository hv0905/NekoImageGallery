if __name__ == '__main__':
    import sys
    sys.path.insert(1, './')

import asyncio
import shutil

import app.config as config
from app.Services import clip_service, db_context
from app.Models.img_data import ImageData
from pathlib import Path
from PIL import Image
from uuid import uuid4
import argparse
from datetime import datetime
from loguru import logger
from shutil import copy2


def parse_args():
    parser = argparse.ArgumentParser(description='Create Qdrant collection')
    parser.add_argument('--copy-from', type=str, required=True, help="Copy from this directory")
    return parser.parse_args()


def copy_and_index(filePath: Path) -> ImageData | None:
    try:
        img = Image.open(filePath)
    except Exception as e:
        logger.error("Error when opening image {}: {}", filePath, e)
        return None
    id = uuid4()
    img_ext = filePath.suffix
    image_vector = clip_service.get_image_vector(img)
    imgdata = ImageData(id=id, url=f'/static/{id}{img_ext}', image_vector=image_vector, index_date=datetime.now())

    # copy to static
    copy2(filePath, Path(config.STATIC_FILE_PATH) / f'{id}{img_ext}')
    return imgdata


async def main(args):
    root = Path(args.copy_from)
    buffer = []
    counter = 0
    for item in root.glob('**/*.*'):
        counter += 1
        logger.info("[{}] Indexing {}", str(counter), item.relative_to(root).__str__())
        if item.suffix in ['.jpg', '.png', '.jpeg']:
            imgdata = copy_and_index(item)
            if imgdata is not None:
                buffer.append(imgdata)
            if len(buffer) >= 20:
                logger.info("Upload {} element to database", len(buffer))
                await db_context.insertItems(buffer)
                buffer.clear()
        else:
            logger.warning("Unsupported file type: {}. Skip...", item.suffix)
    if len(buffer) > 0:
        logger.info("Upload {} element to database", len(buffer))
        await db_context.insertItems(buffer)
        logger.success("Indexing completed! {} images indexed", counter)

if __name__ == '__main__':
    args = parse_args()
    asyncio.run(main(args))
