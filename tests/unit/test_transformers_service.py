from PIL import Image

from app.Services.transformers_service import TransformersService
from app.util.calculate_vectors_cosine import calculate_vectors_cosine
from ..assets import assets_path


class TestTransformersService:

    def setup_class(self):
        self.transformers_service = TransformersService()

    def test_get_image_vector(self):
        vector1 = self.transformers_service.get_image_vector(Image.open(assets_path / 'test_images/cat_0.jpg'))
        vector2 = self.transformers_service.get_image_vector(Image.open(assets_path / 'test_images/cat_1.jpg'))
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

    def test_get_bert_vector_long_text(self):
        vector1 = self.transformers_service.get_bert_vector('The quick brown fox jumps over the lazy dog ' * 100)
        vector2 = self.transformers_service.get_bert_vector('我可以吞下玻璃而不伤身体' * 100)
        assert vector1.shape == (768,)
        assert vector2.shape == (768,)
