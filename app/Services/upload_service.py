import asyncio
from io import BytesIO

from PIL import Image
from loguru import logger

from app.Models.img_data import ImageData
from app.Services.index_service import IndexService
from app.Services.storage import StorageService
from app.Services.vector_db_context import VectorDbContext


class UploadService:
    def __init__(self, storage_service: StorageService, db_context: VectorDbContext, index_service: IndexService):
        self._storage_service = storage_service
        self._db_context = db_context
        self._index_service = index_service

        self._queue = asyncio.Queue(200)
        self._upload_worker_task = asyncio.create_task(self._upload_worker())

    async def _upload_worker(self):
        while True:
            img, img_data, img_bytes, skip_ocr = await self._queue.get()
            try:
                await self._upload_task(img, img_data, img_bytes, skip_ocr)
                logger.success("Image {} uploaded and indexed. Queue Length: {} [-1]", img_data.id, self._queue.qsize())
            except Exception as ex:
                logger.error("Error occurred while uploading image {}", img_data.id)
                logger.exception(ex)
            finally:
                self._queue.task_done()

    async def _upload_task(self, img: Image.Image, img_data: ImageData, img_bytes: bytes, skip_ocr: bool):
        logger.info('Start indexing image {}. Local: {}. Size: {}', img_data.id, img_data.local, len(img_bytes))
        file_name = f"{img_data.id}.{img_data.format}"
        thumb_path = f"thumbnails/{img_data.id}.webp"
        img_thumb = None
        if img_data.local:
            img_data.url = await self._storage_service.active_storage.url(file_name)
            if len(img_bytes) > 1024 * 500:
                img_thumb = img.copy()
                img_data.thumbnail_url = await self._storage_service.active_storage.url(
                    f"thumbnails/{img_data.id}.webp")

        await self._index_service.index_image(img, img_data, skip_ocr=skip_ocr,
                                              background=True)  # The img might be modified after calling this
        logger.success("Image {} indexed.", img_data.id)

        if img_data.local:
            logger.info("Start uploading image {} to local storage.", img_data.id)
            await self._storage_service.active_storage.upload(img_bytes, file_name)
            logger.success("Image {} uploaded to local storage.", img_data.id)
            if len(img_bytes) > 1024 * 500:
                img_thumb.thumbnail((256, 256), resample=Image.Resampling.LANCZOS)
                img_byte_arr = BytesIO()
                img_thumb.save(img_byte_arr, 'WebP')
                await self._storage_service.active_storage.upload(img_byte_arr.getvalue(), thumb_path)
                logger.success("Thumbnail for {} generated and uploaded!", img_data.id)

    async def upload_image(self, img: Image.Image, img_data: ImageData, img_bytes: bytes, skip_ocr: bool):
        await self._queue.put((img, img_data, img_bytes, skip_ocr))
        logger.info("Image {} added to upload queue. Queue Length: {} [+1]", img_data.id, self._queue.qsize())
