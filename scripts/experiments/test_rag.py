from backend.engine.search_engine import SearchEngine
from backend.rag import RAGPipeline


def main():

    engine = SearchEngine(
        "data/raw/sample_documents.json"
    )

    engine.load()

    rag = RAGPipeline()

    while True:

        query = input("\nQuestion (exit to quit): ")

        if query.lower() == "exit":
            break

        results = engine.search(query)

        response = rag.generate_answer(
            query,
            results
        )

        print("\n" + "=" * 70)
        print("QUESTION")
        print("=" * 70)
        print(response["query"])

        print("\n" + "=" * 70)
        print("AI ANSWER")
        print("=" * 70)
        print(response["answer"])

        print("\n" + "=" * 70)
        print("SOURCES")
        print("=" * 70)

        for source in response["sources"]:

            print(f"- {source['text']}")


if __name__ == "__main__":
    main()