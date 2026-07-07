from backend.embeddings import (
    EmbeddingCache,
    FAISSIndexer
)


class PersistenceManager:

    def __init__(self):

        self.embedding_cache = EmbeddingCache()

    def save(

        self,

        embeddings,

        faiss_indexer

    ):

        self.embedding_cache.save(
            embeddings
        )

        faiss_indexer.save()

    def load_embeddings(self):

        return self.embedding_cache.load()

    def embedding_exists(self):

        return self.embedding_cache.exists()