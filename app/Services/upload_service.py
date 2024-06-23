import asyncio
import gc
from io import BytesIO

from PIL import Image
from loguru import logger

from app.Models.api_models.admin_query_params import UploadImageThumbnailMode
from app.Models.img_data import ImageData
from app.Services.index_service import IndexService
from app.Services.storage import StorageService
from app.Services.vector_db_context import VectorDbContext
from app.config import config


class UploadService:
    def __init__(self, storage_service: StorageService, db_context: VectorDbContext, index_service: IndexService):
        self._storage_service = storage_service
        self._db_context = db_context
        self._index_service = index_service

        self._queue = asyncio.Queue(config.admin_index_queue_max_length)
        self._upload_worker_task = asyncio.create_task(self._upload_worker())

        self.uploading_ids = set()
        self._processed_count = 0

    async def _upload_worker(self):
        while True:
            img_data, *args = await self._queue.get()
            try:
                await self._upload_task(img_data, *args)
                logger.success("Image {} uploaded and indexed. Queue Length: {} [-1]", img_data.id, self._queue.qsize())
            except Exception as ex:
                logger.error("Error occurred while uploading image {}", img_data.id)
                logger.exception(ex)
            finally:
                self._queue.task_done()
                self.uploading_ids.remove(img_data.id)
                self._processed_count += 1
                if self._processed_count % 50 == 0:
                    gc.collect()

    async def _upload_task(self, img_data: ImageData, img_bytes: bytes, skip_ocr: bool,
                           thumbnail_mode: UploadImageThumbnailMode):
        img = Image.open(BytesIO(img_bytes))
        logger.info('Start indexing image {}. Local: {}. Size: {}', img_data.id, img_data.local, len(img_bytes))
        file_name = f"{img_data.id}.{img_data.format}"
        thumb_path = f"thumbnails/{img_data.id}.webp"
        gen_thumb = thumbnail_mode == UploadImageThumbnailMode.ALWAYS or (
                thumbnail_mode == UploadImageThumbnailMode.IF_NECESSARY and len(img_bytes) > 1024 * 500)

        if img_data.local:
            img_data.url = await self._storage_service.active_storage.url(file_name)
        if gen_thumb:
            img_data.thumbnail_url = await self._storage_service.active_storage.url(
                f"thumbnails/{img_data.id}.webp")
            img_data.local_thumbnail = True

        await self._index_service.index_image(img, img_data, skip_ocr=skip_ocr, background=True)
        logger.success("Image {} indexed.", img_data.id)

        if img_data.local:
            logger.info("Start uploading image {} to local storage.", img_data.id)
            await self._storage_service.active_storage.upload(img_bytes, file_name)
            logger.success("Image {} uploaded to local storage.", img_data.id)
        if gen_thumb:
            logger.info("Start generate and upload thumbnail for {}.", img_data.id)
            img.thumbnail((256, 256), resample=Image.Resampling.LANCZOS)
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, 'WebP', save_all=True)
            await self._storage_service.active_storage.upload(img_byte_arr.getvalue(), thumb_path)
            logger.success("Thumbnail for {} generated and uploaded!", img_data.id)

        img.close()

    async def upload_image(self, img_data: ImageData, img_bytes: bytes, skip_ocr: bool,
                           thumbnail_mode: UploadImageThumbnailMode):
        self.uploading_ids.add(img_data.id)
        await self._queue.put((img_data, img_bytes, skip_ocr, thumbnail_mode))
        logger.success("Image {} added to upload queue. Queue Length: {} [+1]", img_data.id, self._queue.qsize())

    def get_queue_size(self):
        return self._queue.qsize()
