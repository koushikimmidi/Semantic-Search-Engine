from backend.preprocessing.pipeline import PreprocessingPipeline
from backend.retrieval.bm25 import BM25Retriever
from backend.embeddings.encoder import EmbeddingEncoder
from backend.embeddings.indexer import FAISSIndexer
from backend.embeddings.search import SemanticSearcher
from backend.hybrid.hybrid_search import HybridSearch


def main():

    pipeline = PreprocessingPipeline("data/raw/sample_documents.json")
    processed_docs = pipeline.process()

    documents = [doc["text"] for doc in processed_docs]
    tokenized_docs = [doc["tokens"] for doc in processed_docs]

    bm25 = BM25Retriever(tokenized_docs)

    encoder = EmbeddingEncoder()
    embeddings = encoder.encode(documents)

    indexer = FAISSIndexer(embeddings.shape[1])
    indexer.build(embeddings)

    searcher = SemanticSearcher(
        encoder,
        indexer.index
    )

    hybrid = HybridSearch(
        bm25,
        searcher
    )

    while True:

        query = input("\nEnter Query (exit to quit): ")

        if query.lower() == "exit":
            break

        # BM25
        bm25_results = bm25.search(
            query.lower().split(),
            top_k=5
        )

        bm25_ids = [processed_docs[idx]["id"] for idx, _ in bm25_results]

        # Dense
        distances, indices = searcher.search(
            query,
            top_k=5
        )

        dense_ids = [processed_docs[i]["id"] for i in indices]

        # Hybrid
        hybrid_results = hybrid.search(
            bm25_ids,
            dense_ids
        )

        print("\n" + "=" * 60)
        print("BM25 RESULTS")
        print("=" * 60)

        for rank, (idx, score) in enumerate(bm25_results, start=1):

            print(f"{rank}. {documents[idx]}")
            print(f"Score : {score:.4f}\n")

        print("=" * 60)
        print("DENSE RESULTS")
        print("=" * 60)

        for rank, (distance, index) in enumerate(zip(distances, indices), start=1):

            print(f"{rank}. {documents[index]}")
            print(f"Distance : {distance:.4f}\n")

        print("=" * 60)
        print("HYBRID RESULTS")
        print("=" * 60)

        for rank, (doc_id, score) in enumerate(hybrid_results, start=1):

            document = next(
                d["text"]
                for d in processed_docs
                if d["id"] == doc_id
            )

            print(f"{rank}. {document}")
            print(f"RRF Score : {score:.6f}\n")


if __name__ == "__main__":
    main()