from backend.preprocessing.pipeline import PreprocessingPipeline
from backend.retrieval.bm25 import BM25Retriever
from backend.embeddings.encoder import EmbeddingEncoder
from backend.embeddings.indexer import FAISSIndexer
from backend.embeddings.search import SemanticSearcher
from backend.hybrid.hybrid_search import HybridSearch


def main():

    # ---------------- Load Documents ----------------
    pipeline = PreprocessingPipeline(
        "data/raw/sample_documents.json"
    )

    processed_docs = pipeline.process()

    documents = [
        doc["text"]
        for doc in processed_docs
    ]

    tokenized_docs = [
        doc["tokens"]
        for doc in processed_docs
    ]

    # ---------------- BM25 ----------------
    bm25 = BM25Retriever(
        tokenized_docs
    )

    query = input("Enter Query : ")

    query_tokens = query.lower().split()

    bm25_results = bm25.search(
        query_tokens,
        top_k=len(documents)
    )

    bm25_ids = [
        processed_docs[index]["id"]
        for index, score in bm25_results
    ]

    # ---------------- Dense Search ----------------
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

    searcher = SemanticSearcher(
        encoder,
        indexer.index
    )

    distances, indices = searcher.search(
        query,
        top_k=len(documents)
    )

    dense_ids = [
        processed_docs[index]["id"]
        for index in indices
    ]

    # ---------------- Hybrid Search ----------------
    hybrid = HybridSearch(
        bm25,
        searcher
    )

    ranked_results = hybrid.search(
        bm25_ids,
        dense_ids,
        processed_docs
    )

    # ---------------- Display Results ----------------
    print()
    print("=" * 60)
    print("HYBRID SEARCH RESULTS")
    print("=" * 60)

    for result in ranked_results:

        print()

        print(f"Rank        : {result['rank']}")
        print(f"Document ID : {result['id']}")
        print(f"RRF Score   : {result['score']:.6f}")
        print(f"Text        : {result['text']}")

    print()
    print("Search Completed Successfully!")


if __name__ == "__main__":
    main()