from time import time

import numpy as np
import torch
from PIL import Image
from loguru import logger
from numpy import ndarray
from torch import FloatTensor, no_grad
from transformers import CLIPProcessor, CLIPModel, BertTokenizer, BertModel

from app.config import config


class TransformersService:
    def __init__(self):
        self.device = config.device
        if self.device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Using device: {}; CLIP Model: {}, BERT Model: {}",
                    self.device, config.model.clip, config.model.bert)
        self._clip_model = CLIPModel.from_pretrained(config.model.clip).to(self.device)
        self._clip_processor = CLIPProcessor.from_pretrained(config.model.clip)
        logger.success("CLIP Model loaded successfully")
        if config.ocr_search.enable:
            self._bert_model = BertModel.from_pretrained(config.model.bert).to(self.device)
            self._bert_tokenizer = BertTokenizer.from_pretrained(config.model.bert)
            logger.success("BERT Model loaded successfully")
        else:
            logger.info("OCR search is disabled. Skipping OCR and BERT model loading.")

    @no_grad()
    def get_image_vector(self, image: Image.Image) -> ndarray:
        if image.mode != "RGB":
            image = image.convert("RGB")
        logger.info("Processing image...")
        start_time = time()
        inputs = self._clip_processor(images=image, return_tensors="pt").to(self.device)
        logger.success("Image processed, now Inferring with CLIP model...")
        outputs: FloatTensor = self._clip_model.get_image_features(**inputs)
        logger.success("Inference done. Time elapsed: {:.2f}s", time() - start_time)
        outputs /= outputs.norm(dim=-1, keepdim=True)
        return outputs.numpy(force=True).reshape(-1)

    @no_grad()
    def get_text_vector(self, text: str) -> ndarray:
        logger.info("Processing text...")
        start_time = time()
        inputs = self._clip_processor(text=text, return_tensors="pt").to(self.device)
        logger.success("Text processed, now Inferring with CLIP model...")
        outputs: FloatTensor = self._clip_model.get_text_features(**inputs)
        logger.success("Inference done. Time elapsed: {:.2f}s", time() - start_time)
        outputs /= outputs.norm(dim=-1, keepdim=True)
        return outputs.numpy(force=True).reshape(-1)

    @no_grad()
    def get_bert_vector(self, text: str) -> ndarray:
        start_time = time()
        logger.info("Inferring with BERT model...")
        inputs = self._bert_tokenizer(text.strip().lower(), return_tensors="pt", truncation=True).to(self.device)
        outputs = self._bert_model(**inputs)
        vector = outputs.last_hidden_state.mean(dim=1).squeeze()
        logger.success("BERT inference done. Time elapsed: {:.2f}s", time() - start_time)
        return vector.cpu().numpy()

    @staticmethod
    def get_random_vector() -> ndarray:
        vec = np.random.rand(768)
        vec -= vec.mean()
        return vec
