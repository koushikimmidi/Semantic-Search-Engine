import os
import numpy as np


class EmbeddingCache:

    def __init__(self):

        self.cache_file = "data/embeddings/embeddings.npy"

        os.makedirs(
            "data/embeddings",
            exist_ok=True
        )

    def save(self, embeddings):

        np.save(
            self.cache_file,
            embeddings
        )

    def load(self):

        return np.load(
            self.cache_file
        )

    def exists(self):

        return os.path.exists(
            self.cache_file
        )