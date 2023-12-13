if __name__ == '__main__':
    import sys

    sys.path.insert(1, './')

import argparse
import asyncio
from datetime import datetime
from pathlib import Path
from shutil import copy2
from uuid import uuid4

from PIL import Image
from loguru import logger

from app.Models.img_data import ImageData
from app.Services import transformers_service, db_context
from app.config import config


def parse_args():
    parser = argparse.ArgumentParser(description='Create Qdrant collection')
    parser.add_argument('--copy-from', dest="local_index_target_dir", type=str, required=True,
                        help="Copy from this directory")
    return parser.parse_args()


def copy_and_index(filePath: Path) -> ImageData | None:
    try:
        img = Image.open(filePath)
    except Exception as e:
        logger.error("Error when opening image {}: {}", filePath, e)
        return None
    id = uuid4()
    img_ext = filePath.suffix
    image_ocr_result = None
    text_contain_vector = None
    try:
        image_vector = transformers_service.get_image_vector(img)
        if config.ocr_search.enable:
            image_ocr_result = transformers_service.get_picture_ocr_result(img).strip()
            if image_ocr_result != "":
                text_contain_vector = transformers_service.get_bert_vector(image_ocr_result)
            else:
                image_ocr_result = None

    except Exception as e:
        logger.error("Error when processing image {}: {}", filePath, e)
        return None
    imgdata = ImageData(id=id,
                        url=f'/static/{id}{img_ext}',
                        image_vector=image_vector,
                        text_contain_vector=text_contain_vector,
                        index_date=datetime.now(),
                        ocr_text=image_ocr_result)

    # copy to static
    copy2(filePath, Path(config.static_file.path) / f'{id}{img_ext}')
    return imgdata


@logger.catch()
async def main(args):
    root = Path(args.local_index_target_dir)
    static_path = Path(config.static_file.path)
    if not static_path.exists():
        static_path.mkdir()
    buffer = []
    counter = 0
    for item in root.glob('**/*.*'):
        counter += 1
        logger.info("[{}] Indexing {}", str(counter), item.relative_to(root).__str__())
        if item.suffix in ['.jpg', '.png', '.jpeg', '.jfif', '.webp']:
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
