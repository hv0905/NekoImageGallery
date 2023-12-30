from PIL import Image

from app.Models.img_data import ImageData
from app.Services.ocr_services import OCRService
from app.Services.transformers_service import TransformersService
from app.Services.vector_db_context import VectorDbContext, PointNotFoundError
from app.config import config


class PointDuplicateError(ValueError):
    pass


class IndexService:
    def __init__(self, ocr_service: OCRService, transformers_service: TransformersService, db_context: VectorDbContext):
        self._ocr_service = ocr_service
        self._transformers_service = transformers_service
        self._db_context = db_context

    def _prepare_image(self, image: Image.Image, image_data: ImageData, skip_ocr=False):
        image_data.width = image.width
        image_data.height = image.height
        image_data.aspect_ratio = float(image.width) / image.height

        if image.mode != 'RGB':
            image = image.convert('RGB')  # to reduce convert in next steps
        image_data.image_vector = self._transformers_service.get_image_vector(image)
        if not skip_ocr and config.ocr_search.enable:
            image_data.ocr_text = self._ocr_service.ocr_interface(image)
            if image_data.ocr_text != "":
                image_data.text_contain_vector = self._transformers_service.get_bert_vector(image_data.ocr_text)
            else:
                image_data.ocr_text = None

    # currently, here only need just a simple check
    async def _is_point_duplicate(self, image_data: list[ImageData]) -> bool:
        image_id_list = [str(item.id) for item in image_data]
        try:
            _ = await self._db_context.retrieve_by_ids(image_id_list)
        except PointNotFoundError:
            return True  # Only if all points are not found, then it is not duplicate
        return False

    async def index_image(self, image: Image.Image, image_data: ImageData, skip_ocr=False, allow_overwrite=False):
        if not allow_overwrite or (await self._is_point_duplicate([image_data])):
            raise PointDuplicateError("The uploaded points are contained in the database!")
        self._prepare_image(image, image_data, skip_ocr)
        await self._db_context.insertItems([image_data])

    async def index_image_batch(self, image: list[Image.Image], image_data: list[ImageData],
                                skip_ocr=False, allow_overwrite=False):
        if not allow_overwrite or (await self._is_point_duplicate(image_data)):
            raise PointDuplicateError("The uploaded points are contained in the database!")
        for i, img in enumerate(image):
            self._prepare_image(img, image_data[i], skip_ocr)
        await self._db_context.insertItems(image_data)
