import easyocr
import numpy.random
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel, BertTokenizer, BertModel
from torch import FloatTensor, no_grad
from app.config import config
from loguru import logger
from time import time
from numpy import ndarray


class Service:
    def __init__(self):
        self.device = config.clip.device
        if self.device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Using device: {}; Model: {}", self.device, config.clip.model)
        self.model = CLIPModel.from_pretrained(config.clip.model).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(config.clip.model)
        logger.success("CLIP Model loaded successfully")
        self.bert_tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
        self.bert_model = BertModel.from_pretrained('bert-base-chinese').to(self.device)
        logger.success("BERT Model loaded successfully")
        self.ocrReader = easyocr.Reader(['ch_sim'], gpu=True)
        logger.success("easyOCR loaded successfully")

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
    def get_picture_to_text(self, filePath: str) -> str:
        start_time = time()
        logger.info("Processing text with EasyOCR...")
        ocrResult = self.ocrReader.readtext(filePath)
        pureText = "".join(itm[1] for itm in ocrResult)
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
        vec = numpy.random.rand(768)
        vec -= vec.mean()
        return vec
