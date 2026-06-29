from backend.reranker import CrossEncoderRanker


def main():

    query = "What is Artificial Intelligence?"

    documents = [

        "Machine Learning is a subset of AI.",

        "Python is a programming language.",

        "Artificial Intelligence enables machines to think.",

        "Football is a popular sport.",

        "Deep Learning is based on neural networks."
    ]

    ranker = CrossEncoderRanker()

    results = ranker.rerank(
        query,
        documents
    )

    print()

    print("=" * 60)

    print("CROSS ENCODER RESULTS")

    print("=" * 60)

    for rank, (document, score) in enumerate(results, start=1):

        print()

        print(f"Rank : {rank}")

        print(f"Score : {score:.4f}")

        print(document)


if __name__ == "__main__":
    main()