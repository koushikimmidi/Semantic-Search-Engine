import os

import faiss
import numpy as np


class FAISSIndexer:
    """
    metric="l2"     -> IndexFlatL2 on raw vectors (original behaviour)
    metric="cosine" -> vectors are L2-normalised and searched with
                       inner product, i.e. cosine similarity, which
                       is what sentence-transformer models are
                       trained for.
    """

    def __init__(self, dimension, metric="l2"):

        self.dimension = dimension
        self.metric = metric

        if metric == "cosine":
            self.index = faiss.IndexFlatIP(dimension)
        else:
            self.index = faiss.IndexFlatL2(dimension)

    def build(self, embeddings):

        embeddings = np.ascontiguousarray(embeddings, dtype="float32")

        if self.metric == "cosine":
            faiss.normalize_L2(embeddings)

        self.index.add(embeddings)

    def save(self, path="data/index/faiss.index"):

        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        faiss.write_index(self.index, path)

    def load(self, path="data/index/faiss.index"):

        self.index = faiss.read_index(path)

    def exists(self, path="data/index/faiss.index"):

        return os.path.exists(path)
