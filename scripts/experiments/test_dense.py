from backend.preprocessing.loader import DataLoader
from backend.retrieval.dense import DenseRetriever


def main():

    loader = DataLoader("data/raw/sample_documents.json")

    documents = loader.load_documents()

    retriever = DenseRetriever(documents)

    while True:

        query = input("\nEnter Query (type exit to quit): ")

        if query.lower() == "exit":
            break

        results = retriever.search(query)

        print("\nSemantic Search Results\n")

        for rank, doc in enumerate(results, start=1):

            print(f"Rank : {rank}")
            print(f"Document ID : {doc['id']}")
            print(f"Distance : {doc['distance']:.4f}")
            print(f"Text : {doc['text']}")
            print("-" * 60)


if __name__ == "__main__":
    main()