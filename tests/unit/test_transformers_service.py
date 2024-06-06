from pathlib import Path

from PIL import Image

from app.Services.transformers_service import TransformersService
from app.util.calculate_vectors_cosine import calculate_vectors_cosine


class TestTransformersService:

    def setup_class(self):
        self.transformers_service = TransformersService()
        self.assets_root = Path(__file__).parent / '..' / 'assets'

    def test_get_image_vector(self):
        vector1 = self.transformers_service.get_image_vector(Image.open(self.assets_root / 'test_images/cat_0.jpg'))
        vector2 = self.transformers_service.get_image_vector(Image.open(self.assets_root / 'test_images/cat_1.jpg'))
        assert vector1.shape == (768,)
        assert vector2.shape == (768,)
        assert calculate_vectors_cosine(vector1, vector2) > 0.8

    def test_get_text_vector(self):
        vector1 = self.transformers_service.get_text_vector('1girl')
        vector2 = self.transformers_service.get_text_vector('girl, solo')
        assert vector1.shape == (768,)
        assert vector2.shape == (768,)
        assert calculate_vectors_cosine(vector1, vector2) > 0.8

    def test_get_bert_vector(self):
        vector1 = self.transformers_service.get_bert_vector('hi')
        vector2 = self.transformers_service.get_bert_vector('hello')
        assert vector1.shape == (768,)
        assert vector2.shape == (768,)
        assert calculate_vectors_cosine(vector1, vector2) > 0.8
