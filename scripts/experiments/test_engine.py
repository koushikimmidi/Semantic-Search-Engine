from backend.engine.search_engine import SearchEngine


def main():

    engine = SearchEngine(
        "data/raw/sample_documents.json"
    )

    engine.load()

    while True:

        query = input("\nSearch (type exit to quit): ")

        if query.lower() == "exit":
            break

        results = engine.search(query)

        print("\n" + "=" * 60)
        print("SEARCH RESULTS")
        print("=" * 60)

        for result in results:

            print()

            print(f"Rank : {result['rank']}")
            print(f"Document ID : {result['id']}")
            print(f"Score : {result['score']:.6f}")
            print(f"Text : {result['text']}")


if __name__ == "__main__":
    main()