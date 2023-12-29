from .index_service import IndexService
from .transformers_service import TransformersService
from .vector_db_context import VectorDbContext
from ..config import config, environment

transformers_service = TransformersService()
db_context = VectorDbContext()
ocr_service = None

if environment.local_indexing:
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

index_service = IndexService(ocr_service, transformers_service, db_context)
