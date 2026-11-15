import time

from backend.engine.search_engine import SearchEngine


def main():

    engine = SearchEngine(
        "data/raw/sample_documents.json"
    )

    start = time.perf_counter()

    engine.load()

    end = time.perf_counter()

    print()

    print(f"Initialization Time : {end - start:.4f} seconds")

    while True:

        query = input("\nSearch (exit to quit): ")

        if query.lower() == "exit":
            break

        start = time.perf_counter()

        results = engine.search(query)

        end = time.perf_counter()

        print()

        print(f"Search Time : {end - start:.4f} seconds")

        print("-" * 60)

        for result in results:

            print(f"Rank : {result['rank']}")
            print(f"Score : {result['score']:.6f}")
            print(result["text"])
            print()


if __name__ == "__main__":
    main()