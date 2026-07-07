from backend.engine.search_engine import SearchEngine


def main():

    engine = SearchEngine(
        "data/raw/sample_documents.json"
    )

    engine.load()

    results = engine.search(

        "Artificial Intelligence",

        extension=".txt"

    )

    print()

    print("=" * 60)
    print("FILTERED SEARCH")
    print("=" * 60)

    for result in results:

        print()

        print(result)


if __name__ == "__main__":
    main()