from pathlib import Path

from loguru import logger

from app.config import config, environment

static_dir = None
thumbnails_dir = None
deleted_dir = None


def init():
    global static_dir, thumbnails_dir, deleted_dir
    static_dir = Path(config.static_file.path)
    thumbnails_dir = static_dir / "thumbnails"
    deleted_dir = static_dir / "_deleted"

    if not static_dir.is_dir():
        static_dir.mkdir(parents=True)
        logger.warning(f"static_dir {static_dir} not found, created.")
    if not thumbnails_dir.is_dir():
        thumbnails_dir.mkdir(parents=True)
        logger.warning(f"thumbnails_dir {thumbnails_dir} not found, created.")
    if not deleted_dir.is_dir():
        deleted_dir.mkdir(parents=True)
        logger.warning(f"deleted_dir {deleted_dir} not found, created.")


if config.static_file.enable or environment.local_indexing:
    init()
