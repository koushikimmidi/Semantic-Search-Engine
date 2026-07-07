from backend.indexing import DocumentIndexer

from backend.embeddings import (
    EmbeddingEncoder,
    FAISSIndexer
)

from backend.persistence import PersistenceManager


class IngestionPipeline:

    def __init__(self):

        self.indexer = DocumentIndexer()

        self.encoder = EmbeddingEncoder()

        self.persistence = PersistenceManager()

        self.faiss = None

    def build(self, folder_path):

        documents = self.indexer.index_folder(
            folder_path
        )

        texts = [
            doc["text"]
            for doc in documents
        ]

        if len(texts) == 0:

            print()

            print("Loading cached embeddings...")

            if not self.persistence.embedding_exists():

                print("No embedding cache found.")

                return None

            embeddings = self.persistence.load_embeddings()

        else:

            print()

            print("Generating embeddings...")

            embeddings = self.encoder.encode(
                texts
            )

        self.faiss = FAISSIndexer(
            embeddings.shape[1]
        )

        self.faiss.build(
            embeddings
        )

        self.persistence.save(
            embeddings,
            self.faiss
        )

        print()

        print("=" * 60)
        print("INGESTION COMPLETE")
        print("=" * 60)

        print(
            f"Vectors : {self.faiss.index.ntotal}"
        )

        return {

            "documents": documents,

            "index": self.faiss.index

        }