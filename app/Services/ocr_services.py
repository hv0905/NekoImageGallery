from time import time

import numpy as np
import torch
from PIL import Image
from loguru import logger

from app.config import config


class OCRService:
    def __init__(self):
        self._device = config.device
        self._easyOCRModule, self._paddleOCRModule = None, None
        if self._device == "auto":
            self._device = "cuda" if torch.cuda.is_available() else "cpu"

    @staticmethod
    def _image_preprocess(img: Image.Image) -> Image.Image:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        if img.size[0] > 1024 or img.size[1] > 1024:
            img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        newImg = Image.new('RGB', (1024, 1024), (0, 0, 0))
        newImg.paste(img, ((1024 - img.size[0]) // 2, (1024 - img.size[1]) // 2))
        return newImg

    def ocr_interface(self, img: Image.Image, need_preprocess=True) -> str:
        pass


class EasyPaddleOCRService(OCRService):
    def __init__(self):
        super().__init__()
        from easypaddleocr import EasyPaddleOCR
        self._paddleOCRModule = EasyPaddleOCR(use_angle_cls=True, needWarmUp=True, devices=self._device)
        logger.success("EasyPaddleOCR loaded successfully")

    def _easy_paddleocr_process(self, img: Image.Image) -> str:
        _, _ocrResult, _ = self._paddleOCRModule.ocr(np.array(img))
        if _ocrResult:
            return "".join(itm[0] for itm in _ocrResult if float(itm[1]) > config.ocr_search.ocr_min_confidence)
        return ""

    def ocr_interface(self, img: Image.Image, need_preprocess=True) -> str:
        start_time = time()
        logger.info(f"Processing text with EasyPaddleOCR...")
        res = self._easy_paddleocr_process(self._image_preprocess(img) if need_preprocess else img)
        logger.success("OCR processed done. Time elapsed: {:.2f}s", time() - start_time)
        return res


class EasyOCRService(OCRService):
    def __init__(self):
        super().__init__()
        # noinspection PyPackageRequirements
        import easyocr
        self._easyOCRModule = easyocr.Reader(config.ocr_search.ocr_language,
                                             gpu=True if self._device == "cuda" else False)
        logger.success("easyOCR loaded successfully")

    def _easyocr_process(self, img: Image.Image) -> str:
        _ocrResult = self._easyOCRModule.readtext(np.array(img))
        return " ".join(itm[1] for itm in _ocrResult if itm[2] > config.ocr_search.ocr_min_confidence)

    def ocr_interface(self, img: Image.Image, need_preprocess=True) -> str:
        start_time = time()
        logger.info(f"Processing text with easyOCR...")
        res = self._easyocr_process(self._image_preprocess(img) if need_preprocess else img)
        logger.success("OCR processed done. Time elapsed: {:.2f}s", time() - start_time)
        return res


class PaddleOCRService(OCRService):
    def __init__(self):
        super().__init__()
        # noinspection PyPackageRequirements
        import paddleocr  # pylint: disable=import-error
        self._paddleOCRModule = paddleocr.PaddleOCR(lang="ch", use_angle_cls=True,
                                                    use_gpu=True if self._device == "cuda" else False)
        logger.success("PaddleOCR loaded successfully")

    def _paddleocr_process(self, img: Image.Image) -> str:
        _ocrResult = self._paddleOCRModule.ocr(np.array(img), cls=True)
        if _ocrResult[0]:
            return "".join(itm[1][0] for itm in _ocrResult[0] if itm[1][1] > config.ocr_search.ocr_min_confidence)
        return ""

    def ocr_interface(self, img: Image.Image, need_preprocess=True) -> str:
        start_time = time()
        logger.info(f"Processing text with PaddleOCR...")
        res = self._paddleocr_process(self._image_preprocess(img) if need_preprocess else img)
        logger.success("OCR processed done. Time elapsed: {:.2f}s", time() - start_time)
        return res


class DisabledOCRService(OCRService):
    def __init__(self):
        super().__init__()
        logger.warning("OCR search is disabled. Skipping OCR model loading.")

    def ocr_interface(self, img: Image.Image, need_preprocess=True) -> str:
        raise NotImplementedError("OCR module is disabled. Consider enable it in config.")
