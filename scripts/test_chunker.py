from backend.chunking import TextChunker


def main():

    text = """
Artificial Intelligence enables machines to perform tasks that normally require human intelligence.

Machine Learning is a subset of Artificial Intelligence.

Deep Learning uses neural networks.

Python is widely used for AI development.

Large Language Models can answer questions using retrieved knowledge.
"""

    chunker = TextChunker(

        chunk_size=80,

        overlap=20

    )

    chunks = chunker.chunk(text)

    print()

    print("=" * 60)

    print("TEXT CHUNKS")

    print("=" * 60)

    for i, chunk in enumerate(chunks, start=1):

        print()

        print(f"Chunk {i}")

        print("-" * 40)

        print(chunk)


if __name__ == "__main__":
    main()