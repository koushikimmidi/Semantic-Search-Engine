import faiss
import numpy as np


class SemanticSearcher:

    def __init__(self, encoder, index, normalize=False):

        self.encoder = encoder
        self.index = index

        # Must match how the index was built (cosine -> True).
        self.normalize = normalize

    def search(self, query, top_k=5):

        query_embedding = np.ascontiguousarray(
            self.encoder.encode([query]),
            dtype="float32"
        )

        if self.normalize:
            faiss.normalize_L2(query_embedding)

        top_k = max(1, min(top_k, self.index.ntotal))

        distances, indices = self.index.search(query_embedding, top_k)

        return distances[0], indices[0]
