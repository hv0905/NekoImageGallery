from PIL import Image

from app.Models.img_data import ImageData
from app.Services import TransformersService
from app.Services.ocr_services import OCRService


class IndexService:
    def __init__(self, ocr_service: OCRService, transformers_service: TransformersService):
        self._ocr_service = ocr_service
        self._transformers_service = transformers_service

    def _calculate_vectors(self):
        pass

    def index_image(self, image: Image.Image, image_data: ImageData):
        pass
