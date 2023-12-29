import argparse
from datetime import datetime
from pathlib import Path
from shutil import copy2
from uuid import uuid4

import PIL
from PIL import Image
from loguru import logger

from app.Models.img_data import ImageData
from app.Services import transformers_service, db_context, ocr_service
from app.config import config


def parse_args():
    parser = argparse.ArgumentParser(description='Create Qdrant collection')
    parser.add_argument('--copy-from', dest="local_index_target_dir", type=str, required=True,
                        help="Copy from this directory")
    return parser.parse_args()


def copy_and_index(file_path: Path) -> ImageData | None:
    try:
        img = Image.open(file_path)
    except PIL.UnidentifiedImageError as e:
        logger.error("Error when opening image {}: {}", file_path, e)
        return None
    image_id = uuid4()
    img_ext = file_path.suffix
    image_ocr_result = None
    text_contain_vector = None
    [width, height] = img.size
    try:
        image_vector = transformers_service.get_image_vector(img)
        if config.ocr_search.enable:
            image_ocr_result = ocr_service.ocr_interface(img)  # This will modify img if you use preprocess!
            if image_ocr_result != "":
                text_contain_vector = transformers_service.get_bert_vector(image_ocr_result)
            else:
                image_ocr_result = None
    except Exception as e:
        logger.error("Error when processing image {}: {}", file_path, e)
        return None
    imgdata = ImageData(id=image_id,
                        url=f'/static/{image_id}{img_ext}',
                        image_vector=image_vector,
                        text_contain_vector=text_contain_vector,
                        index_date=datetime.now(),
                        width=width,
                        height=height,
                        aspect_ratio=float(width) / height,
                        ocr_text=image_ocr_result,
                        local=True)

    # copy to static
    copy2(file_path, Path(config.static_file.path) / f'{image_id}{img_ext}')
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
        logger.info("[{}] Indexing {}", str(counter), str(item.relative_to(root)))
        if item.suffix in ['.jpg', '.png', '.jpeg', '.jfif', '.webp', '.gif']:
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
