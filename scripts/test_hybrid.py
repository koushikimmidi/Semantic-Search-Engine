from backend.hybrid.hybrid_search import HybridSearch


def main():

    # BM25 ranked document IDs
    bm25_ids = [
        1,
        2,
        3,
        4,
        5
    ]

    # Dense Search ranked document IDs
    dense_ids = [
        3,
        1,
        5,
        2,
        4
    ]

    # Sample documents
    processed_docs = [
        {
            "id": 1,
            "text": "Machine Learning is a subset of Artificial Intelligence."
        },
        {
            "id": 2,
            "text": "Python is widely used in Data Science."
        },
        {
            "id": 3,
            "text": "BM25 is a keyword ranking algorithm."
        },
        {
            "id": 4,
            "text": "FastAPI is a modern web framework for Python."
        },
        {
            "id": 5,
            "text": "Neural networks are a core part of deep learning."
        }
    ]

    hybrid = HybridSearch(
        bm25=None,
        dense=None
    )

    results = hybrid.search(
        bm25_ids,
        dense_ids,
        processed_docs
    )

    print("\nHybrid Search Results\n")

    for result in results:

        print(f"Rank        : {result['rank']}")
        print(f"Document ID : {result['id']}")
        print(f"RRF Score   : {result['score']:.6f}")
        print(f"Text        : {result['text']}")
        print("-" * 50)


if __name__ == "__main__":
    main()