from loguru import logger

from .index_service import IndexService
from .storage import StorageService
from .transformers_service import TransformersService
from .upload_service import UploadService
from .vector_db_context import VectorDbContext
from ..config import config, environment


class ServiceProvider:
    def __init__(self):
        self.transformers_service = TransformersService()
        self.db_context = VectorDbContext()
        self.ocr_service = None

        if config.ocr_search.enable and (environment.local_indexing or config.admin_api_enable):
            match config.ocr_search.ocr_module:
                case "easyocr":
                    from .ocr_services import EasyOCRService

                    self.ocr_service = EasyOCRService()
                case "easypaddleocr":
                    from .ocr_services import EasyPaddleOCRService

                    self.ocr_service = EasyPaddleOCRService()
                case "paddleocr":
                    from .ocr_services import PaddleOCRService

                    self.ocr_service = PaddleOCRService()
                case _:
                    raise NotImplementedError(f"OCR module {config.ocr_search.ocr_module} not implemented.")
        else:
            from .ocr_services import DisabledOCRService

            self.ocr_service = DisabledOCRService()
        logger.info(f"OCR service '{type(self.ocr_service).__name__}' initialized.")

        self.index_service = IndexService(self.ocr_service, self.transformers_service, self.db_context)
        self.storage_service = StorageService()
        logger.info(f"Storage service '{type(self.storage_service.active_storage).__name__}' initialized.")

        self.upload_service = None

        if config.admin_api_enable:
            self.upload_service = UploadService(self.storage_service, self.db_context, self.index_service)

    async def onload(self):
        await self.db_context.onload()
