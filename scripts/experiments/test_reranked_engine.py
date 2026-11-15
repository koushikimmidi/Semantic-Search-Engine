from backend.engine.search_engine import SearchEngine


def main():

    engine = SearchEngine(
        "data/raw/sample_documents.json"
    )

    engine.load()

    while True:

        query = input("\nEnter Query (exit to quit): ")

        if query.lower() == "exit":
            break

        results = engine.search(query)

        print("\n")
        print("=" * 70)
        print("FINAL RERANKED RESULTS")
        print("=" * 70)

        for result in results:

            print()

            print(f"Rank : {result['rank']}")
            print(f"Document ID : {result['id']}")
            print(f"Cross Encoder Score : {result['cross_score']:.4f}")
            print(result["text"])


if __name__ == "__main__":
    main()