from backend.embeddings.encoder import EmbeddingEncoder
from backend.embeddings.indexer import FAISSIndexer
from backend.embeddings.search import SemanticSearcher


def main():

    documents = [
        "Machine Learning is amazing.",
        "Artificial Intelligence is the future.",
        "Python is a programming language."
    ]

    encoder = EmbeddingEncoder()

    embeddings = encoder.encode(documents)

    indexer = FAISSIndexer(embeddings.shape[1])

    indexer.build(embeddings)

    searcher = SemanticSearcher(
        encoder,
        indexer.index
    )

    query = "AI"

    distances, indices = searcher.search(
        query,
        top_k=len(documents)
    )

    print("\nSemantic Search Results\n")

    for rank, (distance, index) in enumerate(zip(distances, indices), start=1):

        print(f"{rank}. {documents[index]}")
        print(f"Distance : {distance:.4f}")
        print("-" * 50)


if __name__ == "__main__":
    main()