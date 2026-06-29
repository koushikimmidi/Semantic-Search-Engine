from backend.embeddings.encoder import EmbeddingEncoder
from backend.embeddings.indexer import FAISSIndexer
from backend.embeddings.search import SemanticSearcher


class DenseRetriever:

    def __init__(self, documents):

        self.documents = documents

        self.encoder = EmbeddingEncoder()

        texts = [doc["text"] for doc in documents]

        embeddings = self.encoder.encode(texts)

        self.indexer = FAISSIndexer(embeddings.shape[1])

        self.indexer.build(embeddings)

        self.searcher = SemanticSearcher(
            self.encoder,
            self.indexer.index
        )

    def search(self, query, top_k=5):

        distances, indices = self.searcher.search(
            query,
            top_k=min(top_k, len(self.documents))
        )

        results = []

        for distance, index in zip(distances, indices):

            results.append({

                "id": self.documents[index]["id"],

                "text": self.documents[index]["text"],

                "distance": float(distance)

            })

        return results