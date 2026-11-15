from backend.embeddings.encoder import EmbeddingEncoder
from backend.embeddings.indexer import FAISSIndexer


def main():

    encoder = EmbeddingEncoder()

    documents = [
        "Machine Learning is amazing.",
        "Artificial Intelligence is the future.",
        "Python is a programming language."
    ]

    embeddings = encoder.encode(documents)

    dimension = embeddings.shape[1]

    indexer = FAISSIndexer(dimension)

    indexer.build(embeddings)

    indexer.save("data/embeddings/faiss.index")

    print("Index Created Successfully!")
    print("Total Documents :", indexer.index.ntotal)
    print("Embedding Dimension :", dimension)


if __name__ == "__main__":
    main()