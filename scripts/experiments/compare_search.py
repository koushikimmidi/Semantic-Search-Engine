from backend.preprocessing.pipeline import PreprocessingPipeline
from backend.retrieval.bm25 import BM25Retriever
from backend.retrieval.dense import DenseRetriever


def main():

    pipeline = PreprocessingPipeline(
        "data/raw/sample_documents.json"
    )

    processed_docs = pipeline.process()

    tokenized_docs = [doc["tokens"] for doc in processed_docs]

    bm25 = BM25Retriever(tokenized_docs)

    raw_documents = []

    for doc in processed_docs:
        raw_documents.append({
            "id": doc["id"],
            "text": doc["text"]
        })

    dense = DenseRetriever(raw_documents)

    while True:

        query = input("\nEnter Query (exit to quit): ")

        if query.lower() == "exit":
            break

        print("\n" + "=" * 60)
        print("BM25 RESULTS")
        print("=" * 60)

        bm25_results = bm25.search(query.lower().split())

        for rank, (index, score) in enumerate(bm25_results, start=1):

            print(f"{rank}. Score : {score:.4f}")
            print(raw_documents[index]["text"])
            print()

        print("=" * 60)
        print("DENSE RESULTS")
        print("=" * 60)

        dense_results = dense.search(query)

        for rank, doc in enumerate(dense_results, start=1):

            print(f"{rank}. Distance : {doc['distance']:.4f}")
            print(doc["text"])
            print()


if __name__ == "__main__":
    main()