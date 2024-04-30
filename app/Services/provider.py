from loguru import logger

from .index_service import IndexService
from .storage import StorageService
from .transformers_service import TransformersService
from .upload_service import UploadService
from .vector_db_context import VectorDbContext
from ..config import config, environment

transformers_service = TransformersService()
db_context = VectorDbContext()
ocr_service = None

if environment.local_indexing or config.admin_api_enable:
    match config.ocr_search.ocr_module:
        case "easyocr":
            from .ocr_services import EasyOCRService

            ocr_service = EasyOCRService()
        case "easypaddleocr":
            from .ocr_services import EasyPaddleOCRService

            ocr_service = EasyPaddleOCRService()
        case "paddleocr":
            from .ocr_services import PaddleOCRService

            ocr_service = PaddleOCRService()
        case _:
            raise NotImplementedError(f"OCR module {config.ocr_search.ocr_module} not implemented.")
else:
    from .ocr_services import DisabledOCRService

    ocr_service = DisabledOCRService()
logger.info(f"OCR service '{type(ocr_service).__name__}' initialized.")

index_service = IndexService(ocr_service, transformers_service, db_context)
storage_service = StorageService()
logger.info(f"Storage service '{type(storage_service.active_storage).__name__}' initialized.")

upload_service = None

if config.admin_api_enable:
    upload_service = UploadService(storage_service, db_context, index_service)
