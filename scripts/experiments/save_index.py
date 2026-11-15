from backend.preprocessing.pipeline import PreprocessingPipeline
from backend.embeddings.encoder import EmbeddingEncoder
from backend.embeddings.indexer import FAISSIndexer
from backend.embeddings.storage import IndexStorage


def main():

    pipeline = PreprocessingPipeline(
        "data/raw/sample_documents.json"
    )

    processed = pipeline.process()

    documents = [
        doc["text"]
        for doc in processed
    ]

    encoder = EmbeddingEncoder()

    embeddings = encoder.encode(
        documents
    )

    indexer = FAISSIndexer(
        embeddings.shape[1]
    )

    indexer.build(
        embeddings
    )

    IndexStorage.save(
        indexer.index,
        "data/index/faiss.index"
    )

    print()

    print("FAISS Index Saved Successfully!")



if __name__ == "__main__":
    main()