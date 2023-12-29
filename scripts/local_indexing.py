from datetime import datetime
from pathlib import Path
from shutil import copy2
from uuid import uuid4

import PIL
from PIL import Image
from loguru import logger

from app.Models.img_data import ImageData
from app.Services.provider import index_service
from app.config import config
from .local_utility import gather_valid_files


async def copy_and_index(file_path: Path):
    try:
        img = Image.open(file_path)
    except PIL.UnidentifiedImageError as e:
        logger.error("Error when opening image {}: {}", file_path, e)
        return
    image_id = uuid4()
    img_ext = file_path.suffix
    imgdata = ImageData(id=image_id,
                        url=f'/static/{image_id}{img_ext}',
                        index_date=datetime.now(),
                        local=True)
    try:
        await index_service.index_image(img, imgdata)
    except Exception as e:
        logger.error("Error when processing image {}: {}", file_path, e)
        return
    # copy to static
    copy2(file_path, Path(config.static_file.path) / f'{image_id}{img_ext}')


@logger.catch()
async def main(args):
    root = Path(args.local_index_target_dir)
    static_path = Path(config.static_file.path)
    static_path.mkdir(exist_ok=True)
    counter = 0
    for item in gather_valid_files(root):
        counter += 1
        logger.info("[{}] Indexing {}", str(counter), str(item.relative_to(root)))
        await copy_and_index(item)
    logger.success("Indexing completed! {} images indexed", counter)
