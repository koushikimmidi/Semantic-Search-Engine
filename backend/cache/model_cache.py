from sentence_transformers import SentenceTransformer
from backend.config import Settings


class ModelCache:

    _model = None

    @classmethod
    def get_model(cls):

        if cls._model is None:

            print("Loading SentenceTransformer Model...")

            cls._model = SentenceTransformer(
                Settings.EMBEDDING_MODEL
            )

        return cls._model