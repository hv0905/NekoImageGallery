from loguru import logger

from app.Services import db_context, transformers_service

CURRENT_VERSION = 2


async def migrate_v1_v2():
    logger.info("Migrating from v1 to v2...")
    next_id = None
    count = 0
    while True:
        points, next_id = await db_context.scroll_points(next_id, count=100)
        for point in points:
            count += 1
            logger.info("[{}] Migrating point {}", count, point.id)
            if point.ocr_text is not None:
                point.text_contain_vector = transformers_service.get_bert_vector(point.ocr_text_lower)
            if point.url.startswith('/'):
                point.local = True  # V1 database assuming all image with '/' as begins is a local image,
                # v2 migrate to a more strict approach
            await db_context.updatePayload(point)  # store the new ocr_text_lower, vector won't update currently
        logger.info("Updating vectors...")
        await db_context.updateVectors(points)  # Update vectors for this group of points
        if next_id is None:
            break


def migrate(from_version: int):
    match from_version:
        case 1:
            migrate_v1_v2()
        case 2:
            logger.info("Already up to date.")
            pass
        case _:
            raise Exception(f"Unknown version {from_version}")
