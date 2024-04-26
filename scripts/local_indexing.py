import uuid
from datetime import datetime
from pathlib import Path

import PIL
from PIL import Image
from loguru import logger

from app.Models.img_data import ImageData
from app.Services.provider import storage_service
from app.Services.provider import index_service, db_context
from app.util import generate_uuid
from .local_utility import fetch_path_uuid_list

overall_count = 0


async def copy_and_index(file_path: Path, uuid_str: str = None):
    global overall_count
    overall_count += 1
    logger.info("[{}] Indexing {}", str(overall_count), str(file_path))
    try:
        img = Image.open(file_path)
    except PIL.UnidentifiedImageError as e:
        logger.error("Error when opening image {}: {}", file_path, e)
        return
    image_id = uuid.UUID(uuid_str) if uuid_str else generate_uuid.generate(file_path)
    img_ext = file_path.suffix
    imgdata = ImageData(id=image_id,
                        url=await storage_service.active_storage.url(f'{image_id}{img_ext}'),
                        index_date=datetime.now(),
                        format=img_ext,
                        local=True)
    try:
        # This has already been checked for duplicated, so there's no need to double-check.
        await index_service.index_image(img, imgdata, allow_overwrite=True)
    except Exception as e:
        logger.error("Error when processing image {}: {}", file_path, e)
        return
    # copy to static
    await storage_service.active_storage.upload(file_path, f'{image_id}{img_ext}')


async def copy_and_index_batch(file_path_list: list[tuple[Path, str]]):
    for file_path_uuid_tuple in file_path_list:
        await copy_and_index(file_path_uuid_tuple[0], uuid_str=file_path_uuid_tuple[1])


@logger.catch()
async def main(args):
    root = Path(args.local_index_target_dir)
    # First, check if the database is empty
    item_number = await db_context.get_counts(exact=False)
    if item_number == 0:
        # database is empty, do as usual
        logger.warning("The database is empty, Will not check for duplicate points.")
        async for item in storage_service.local_storage.list_files(root, batch_max_files=1):
            await copy_and_index(item[0])
    else:
        # database is not empty, check for duplicate points
        logger.warning("The database is not empty, Will check for duplicate points.")
        async for itm in storage_service.local_storage.list_files(root, batch_max_files=5000):
            local_file_path_with_uuid_list = fetch_path_uuid_list(itm)
            local_file_uuid_list = [itm[1] for itm in local_file_path_with_uuid_list]
            duplicate_uuid_list = await db_context.validate_ids(local_file_uuid_list)
            if len(duplicate_uuid_list) > 0:
                duplicate_uuid_list = set(duplicate_uuid_list)
                local_file_path_with_uuid_list = [item for item in local_file_path_with_uuid_list
                                                  if item[1] not in duplicate_uuid_list]
                logger.info("Found {} duplicate points, of which {} are duplicates in the database. "
                            "The remaining {} points will be indexed.",
                            len(itm) - len(local_file_path_with_uuid_list), len(duplicate_uuid_list),
                            len(local_file_path_with_uuid_list))
            else:
                logger.info("Found {} duplicate points, of which {} are duplicates in the database."
                            " The remaining {} points will be indexed.",
                            0, 0, len(local_file_path_with_uuid_list))
            await copy_and_index_batch(local_file_path_with_uuid_list)

    logger.success("Indexing completed! {} images indexed", overall_count)
