from backend.chunking import TextChunker
from backend.metadata import MetadataBuilder


def main():

    text = """
Artificial Intelligence enables machines to perform tasks.

Machine Learning is a subset of Artificial Intelligence.

Deep Learning uses neural networks.

Python is widely used for AI.
"""

    chunker = TextChunker(
        chunk_size=60,
        overlap=15
    )

    chunks = chunker.chunk(text)

    builder = MetadataBuilder()

    documents = builder.build(
        chunks,
        source="sample.txt",
        page=1
    )

    print()
    print("=" * 60)
    print("DOCUMENT METADATA")
    print("=" * 60)

    for document in documents:
        print()
        print(document)


if __name__ == "__main__":
    main()