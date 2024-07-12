import asyncio
import gc
import io
import pathlib
from io import BytesIO

from PIL import Image
from loguru import logger

from app.Models.api_models.admin_query_params import UploadImageThumbnailMode
from app.Models.errors import PointDuplicateError
from app.Models.mapped_image import MappedImage
from app.Services.index_service import IndexService
from app.Services.lifespan_service import LifespanService
from app.Services.storage import StorageService
from app.Services.vector_db_context import VectorDbContext
from app.config import config
from app.util.generate_uuid import generate_uuid


class UploadService(LifespanService):
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

    async def _upload_task(self, mapped_img: MappedImage, img_bytes: bytes, skip_ocr: bool,
                           thumbnail_mode: UploadImageThumbnailMode):
        img = Image.open(BytesIO(img_bytes))
        logger.info('Start indexing image {}. Local: {}. Size: {}', mapped_img.id, mapped_img.local, len(img_bytes))
        file_name = f"{mapped_img.id}.{mapped_img.format}"
        thumb_path = f"thumbnails/{mapped_img.id}.webp"
        gen_thumb = thumbnail_mode == UploadImageThumbnailMode.ALWAYS or (
                thumbnail_mode == UploadImageThumbnailMode.IF_NECESSARY and len(img_bytes) > 1024 * 500)

        if mapped_img.local:
            mapped_img.url = await self._storage_service.active_storage.url(file_name)
        if gen_thumb:
            mapped_img.thumbnail_url = await self._storage_service.active_storage.url(
                f"thumbnails/{mapped_img.id}.webp")
            mapped_img.local_thumbnail = True

        await self._index_service.index_image(img, mapped_img, skip_ocr=skip_ocr, background=True)
        logger.success("Image {} indexed.", mapped_img.id)

        if mapped_img.local:
            logger.info("Start uploading image {} to local storage.", mapped_img.id)
            await self._storage_service.active_storage.upload(img_bytes, file_name)
            logger.success("Image {} uploaded to local storage.", mapped_img.id)
        if gen_thumb:
            logger.info("Start generate and upload thumbnail for {}.", mapped_img.id)
            img.thumbnail((256, 256), resample=Image.Resampling.LANCZOS)
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, 'WebP', save_all=True)
            await self._storage_service.active_storage.upload(img_byte_arr.getvalue(), thumb_path)
            logger.success("Thumbnail for {} generated and uploaded!", mapped_img.id)

        img.close()

    async def queue_upload_image(self, mapped_img: MappedImage, img_bytes: bytes, skip_ocr: bool,
                                 thumbnail_mode: UploadImageThumbnailMode):
        self.uploading_ids.add(mapped_img.id)
        await self._queue.put((mapped_img, img_bytes, skip_ocr, thumbnail_mode))
        logger.success("Image {} added to upload queue. Queue Length: {} [+1]", mapped_img.id, self._queue.qsize())

    async def assign_image_id(self, img_file: pathlib.Path | io.BytesIO | bytes):
        img_id = generate_uuid(img_file)
        # check for duplicate points
        if img_id in self.uploading_ids or len(await self._db_context.validate_ids([str(img_id)])) != 0:
            logger.warning("Duplicate upload request for image id: {}", img_id)
            raise PointDuplicateError(f"The uploaded point is already contained in the database! entity id: {img_id}",
                                      img_id)
        return img_id

    async def sync_upload_image(self, mapped_img: MappedImage, img_bytes: bytes, skip_ocr: bool,
                                thumbnail_mode: UploadImageThumbnailMode):
        await self._upload_task(mapped_img, img_bytes, skip_ocr, thumbnail_mode)

    def get_queue_size(self):
        return self._queue.qsize()

    async def on_exit(self):  # pragma: no cover  Hard to test in UT.
        if self.get_queue_size() != 0:
            logger.warning("There are still {} images in the upload queue. Waiting for upload process to be completed.",
                           self.get_queue_size())
        await self._queue.join()
