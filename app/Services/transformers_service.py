from time import time

import numpy as np
import torch
from PIL import Image
from loguru import logger
from numpy import ndarray
from torch import FloatTensor, no_grad
from transformers import CLIPProcessor, CLIPModel, BertTokenizer, BertModel

from app.config import config, environment


class Service:
    def __init__(self):
        self.device = config.device
        if self.device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Using device: {}; CLIP Model: {}, BERT Model: {}",
                    self.device, config.clip.model, config.ocr_search.bert_model)

        self.model = CLIPModel.from_pretrained(config.clip.model).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(config.clip.model)
        logger.success("CLIP Model loaded successfully")

        if config.ocr_search.enable:
            self.bert_model = BertModel.from_pretrained(config.ocr_search.bert_model).to(self.device)
            self.bert_tokenizer = BertTokenizer.from_pretrained(config.ocr_search.bert_model)
            logger.success("BERT Model loaded successfully")
            if environment.local_indexing:
                import easyocr
                self.ocrReader = easyocr.Reader(config.ocr_search.ocr_language,
                                                gpu=True if self.device == "cuda" else False)
                logger.success("easyOCR loaded successfully")
        else:
            logger.info("OCR search is disabled. Skipping OCR model loading.")

    @no_grad()
    def get_image_vector(self, image: Image.Image) -> ndarray:
        if image.mode != "RGB":
            image = image.convert("RGB")
        logger.info("Processing image...")
        start_time = time()
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        logger.success("Image processed, now inferencing with CLIP model...")
        outputs: FloatTensor = self.model.get_image_features(**inputs)
        logger.success("Inference done. Time elapsed: {:.2f}s", time() - start_time)
        logger.info("Norm: {}", outputs.norm(dim=-1).item())
        outputs /= outputs.norm(dim=-1, keepdim=True)
        return outputs.numpy(force=True).reshape(-1)

    @no_grad()
    def get_text_vector(self, text: str) -> ndarray:
        logger.info("Processing text...")
        start_time = time()
        inputs = self.processor(text=text, return_tensors="pt").to(self.device)
        logger.success("Text processed, now inferencing with CLIP model...")
        outputs: FloatTensor = self.model.get_text_features(**inputs)
        logger.success("Inference done. Time elapsed: {:.2f}s", time() - start_time)
        logger.info("Norm: {}", outputs.norm(dim=-1).item())
        outputs /= outputs.norm(dim=-1, keepdim=True)
        return outputs.numpy(force=True).reshape(-1)

    @no_grad()
    def get_picture_ocr_result(self, img: Image.Image) -> str:
        start_time = time()
        logger.info("Processing text with EasyOCR...")
        if img.mode != 'RGB':
            img = img.convert('RGB')
        if img.size[0] > 1024 or img.size[1] > 1024:
            img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        newImg = Image.new('RGB', (1024, 1024), (0, 0, 0))
        newImg.paste(img, ((1024 - img.size[0]) // 2, (1024 - img.size[1]) // 2))
        ocrResult = self.ocrReader.readtext(np.array(img))
        pureText = " ".join(itm[1] for itm in ocrResult if itm[2] > config.ocr_search.ocr_min_confidence)
        logger.success("OCR processed done. Time elapsed: {:.2f}s", time() - start_time)
        return pureText

    @no_grad()
    def get_bert_vector(self, text: str) -> ndarray:
        start_time = time()
        logger.info("Inferencing with BERT model...")
        inputs = self.bert_tokenizer(text, return_tensors="pt").to(self.device)
        outputs = self.bert_model(**inputs)
        vector = outputs.last_hidden_state.mean(dim=1).squeeze()
        logger.success("BERT inference done. Time elapsed: {:.2f}s", time() - start_time)
        return vector.cpu().numpy()

    @staticmethod
    def get_random_vector() -> ndarray:
        vec = np.random.rand(768)
        vec -= vec.mean()
        return vec
