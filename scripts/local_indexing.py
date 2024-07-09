import sys
from datetime import datetime
from pathlib import Path

import PIL
from loguru import logger
from rich.progress import Progress

from app.Models.api_models.admin_query_params import UploadImageThumbnailMode
from app.Models.errors import PointDuplicateError
from app.Models.img_data import ImageData
from app.Services.provider import ServiceProvider
from app.util.local_file_utility import glob_local_files

services: ServiceProvider | None = None


async def index_task(file_path: Path, categories: list[str], starred: bool, thumbnail_mode: UploadImageThumbnailMode):
    try:
        img_id = await services.upload_service.assign_image_id(file_path)
        image_data = ImageData(id=img_id,
                               local=True,
                               categories=categories,
                               starred=starred,
                               format=file_path.suffix[1:],  # remove the dot
                               index_date=datetime.now())
        await services.upload_service.sync_upload_image(image_data, file_path.read_bytes(), skip_ocr=False,
                                                        thumbnail_mode=thumbnail_mode)
    except PointDuplicateError as ex:
        logger.warning("Image {} already exists in the database", file_path)
    except PIL.UnidentifiedImageError as e:
        logger.error("Error when processing image {}: {}", file_path, e)


@logger.catch()
async def main(root_directory: list[Path], categories: list[str], starred: bool,
               thumbnail_mode: UploadImageThumbnailMode):
    global services
    services = ServiceProvider()
    await services.onload()
    files = []
    for root in root_directory:
        files.extend(list(glob_local_files(root, '**/*')))
    with Progress() as progress:
        # A workaround for the loguru logger to work with rich progressbar
        logger.remove()
        logger.add(sys.stderr, colorize=True)
        for idx, item in enumerate(progress.track(files, description="Indexing...")):
            logger.info("[{} / {}] Indexing {}", idx + 1, len(files), str(item))

            await index_task(item, categories, starred, thumbnail_mode)

    logger.success("Indexing completed!")
