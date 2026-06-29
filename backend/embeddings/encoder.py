from backend.cache import ModelCache


class EmbeddingEncoder:

    def __init__(self):

        self.model = ModelCache.get_model()

    def encode(self, texts):

        return self.model.encode(
            texts,
            convert_to_numpy=True
        )