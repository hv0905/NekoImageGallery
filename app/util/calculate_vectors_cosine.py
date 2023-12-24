import numpy as np


def calculate_vectors_cosine(image_vector, text_vector):
    return np.dot(image_vector, text_vector) / (np.linalg.norm(image_vector) * np.linalg.norm(text_vector))
