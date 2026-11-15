from backend.reranker import RerankPipeline


def main():

    query = "What is Artificial Intelligence?"

    results = [

        {

            "id": 1,

            "text": "Machine Learning is a subset of AI."

        },

        {

            "id": 2,

            "text": "Python is a programming language."

        },

        {

            "id": 3,

            "text": "Artificial Intelligence enables machines to think."

        },

        {

            "id": 4,

            "text": "Football is a popular sport."

        }

    ]

    reranker = RerankPipeline()

    ranked = reranker.rerank(

        query,

        results

    )

    print()

    print("=" * 60)

    print("RERANKED RESULTS")

    print("=" * 60)

    for result in ranked:

        print()

        print(f"Rank : {result['rank']}")

        print(f"ID : {result['id']}")

        print(f"Score : {result['cross_score']:.4f}")

        print(result["text"])


if __name__ == "__main__":
    main()