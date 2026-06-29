from backend.indexing import DocumentIndexer
from backend.embeddings.encoder import EmbeddingEncoder
from backend.embeddings.indexer import FAISSIndexer


class IngestionPipeline:

    def __init__(self):

        self.indexer = DocumentIndexer()

        self.encoder = EmbeddingEncoder()

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

            print("No new documents found.")

            return None

        embeddings = self.encoder.encode(
            texts
        )

        self.faiss = FAISSIndexer(
            embeddings.shape[1]
        )

        self.faiss.build(
            embeddings
        )

        print()

        print("=" * 60)
        print("INGESTION COMPLETE")
        print("=" * 60)

        print(f"Indexed Chunks : {len(documents)}")

        return {

            "documents": documents,

            "index": self.faiss.index

        }