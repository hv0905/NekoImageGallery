import torch
import numpy as np
from time import time
from PIL import Image
from loguru import logger
from app.config import config, environment


class OCRService:
    def __init__(self):
        self._device = config.device
        self._easyOCRModule, self._paddleOCRModule = None, None
        if self._device == "auto":
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
        if environment.local_indexing:
            if config.ocr_search.ocr_module == "easyocr":
                import easyocr
                self._easyOCRModule = easyocr.Reader(config.ocr_search.ocr_language,
                                                     gpu=True if self._device == "cuda" else False)
                logger.success("easyOCR loaded successfully")
            elif config.ocr_search.ocr_module == "paddleocr":
                import paddleocr
                self._paddleOCRModule = paddleocr.PaddleOCR(lang="ch", use_angle_cls=True,
                                                            use_gpu=True if self._device == "cuda" else False)
                logger.success("PaddleOCR loaded successfully")
            else:
                raise NotImplementedError("Only support easyOCR and PaddleOCR!")
        else:
            logger.warning("OCR search is disabled. Skipping OCR model loading.")

    @staticmethod
    def _image_preprocess(img: Image.Image) -> Image.Image:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        if img.size[0] > 1024 or img.size[1] > 1024:
            img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        newImg = Image.new('RGB', (1024, 1024), (0, 0, 0))
        newImg.paste(img, ((1024 - img.size[0]) // 2, (1024 - img.size[1]) // 2))
        return newImg

    def _paddleocr_process(self, img: Image.Image) -> str:
        _ocrResult = self._paddleOCRModule.ocr(np.array(img), cls=True)
        if _ocrResult[0]:
            return "".join(itm[1][0] for itm in _ocrResult[0] if itm[1][1] > config.ocr_search.ocr_min_confidence)
        return ""

    def _easyocr_process(self, img: Image.Image) -> str:
        _ocrResult = self._easyOCRModule.readtext(np.array(img))
        return " ".join(itm[1] for itm in _ocrResult if itm[2] > config.ocr_search.ocr_min_confidence)

    # so can let user choose whether you need_preprocess
    def ocr_interface(self, img: Image.Image, need_preprocess=True) -> str:
        start_time = time()
        logger.info(f"Processing text with {config.ocr_search.ocr_module}...")
        if config.ocr_search.ocr_module == "easyocr":
            res = self._easyocr_process(self._image_preprocess(img) if need_preprocess else img)
        elif config.ocr_search.ocr_module == "paddleocr":
            res = self._paddleocr_process(self._image_preprocess(img) if need_preprocess else img)
        else:
            raise NotImplementedError("Only support easyOCR and PaddleOCR!")
        logger.success("OCR processed done. Time elapsed: {:.2f}s", time() - start_time)
        return res
