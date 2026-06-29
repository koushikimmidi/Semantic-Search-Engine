import numpy as np


class SemanticSearcher:

    def __init__(self, encoder, index):
        self.encoder = encoder
        self.index = index

    def search(self, query, top_k=5):

        query_embedding = self.encoder.encode([query])

        query_embedding = np.array(query_embedding).astype("float32")

        distances, indices = self.index.search(query_embedding, top_k)

        return distances[0], indices[0]