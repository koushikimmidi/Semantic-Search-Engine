from backend.llm import GemmaLLM


def main():

    llm = GemmaLLM()

    context = """
Machine Learning is a subset of Artificial Intelligence.

Deep Learning uses neural networks.

Python is widely used for AI.
"""

    question = "What is Machine Learning?"

    answer = llm.generate(
        question,
        context
    )

    print()

    print("=" * 60)

    print("GEMMA RESPONSE")

    print("=" * 60)

    print()

    print(answer)


if __name__ == "__main__":
    main()