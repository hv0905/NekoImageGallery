from loguru import logger

from app.Services.provider import ServiceProvider

CURRENT_VERSION = 2

services: ServiceProvider | None = None


async def migrate_v1_v2():
    logger.info("Migrating from v1 to v2...")
    next_id = None
    count = 0
    while True:
        points, next_id = await services.db_context.scroll_points(next_id, count=100)
        for point in points:
            count += 1
            logger.info("[{}] Migrating point {}", count, point.id)
            if point.url.startswith('/'):
                # V1 database assuming all image with '/' as begins is a local image,
                # v2 migrate to a more strict approach
                point.local = True
            await services.db_context.update_payload(point)  # This will also store ocr_text_lower field, if present
            if point.ocr_text is not None:
                point.text_contain_vector = services.transformers_service.get_bert_vector(point.ocr_text_lower)

        logger.info("Updating vectors...")
        # Update vectors for this group of points
        await services.db_context.update_vectors([t for t in points if t.text_contain_vector is not None])
        if next_id is None:
            break


async def migrate(from_version: int):
    global services
    services = ServiceProvider()
    await services.onload()
    match from_version:
        case 1:
            await migrate_v1_v2()
        case 2:
            logger.info("Already up to date.")
        case _:
            raise ValueError(f"Unknown version {from_version}")
