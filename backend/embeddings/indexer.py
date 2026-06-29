import faiss
import numpy as np


class FAISSIndexer:
    """
    Builds and stores a FAISS index.
    """

    def __init__(self, dimension):
        self.index = faiss.IndexFlatL2(dimension)

    def build(self, embeddings):
        embeddings = np.array(embeddings).astype("float32")
        self.index.add(embeddings)

    def save(self, path):
        faiss.write_index(self.index, path)

    def load(self, path):
        self.index = faiss.read_index(path)