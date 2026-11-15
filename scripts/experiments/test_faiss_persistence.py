import numpy as np

from backend.embeddings.indexer import FAISSIndexer


def main():

    embeddings = np.random.rand(
        5,
        384
    ).astype("float32")

    indexer = FAISSIndexer(
        384
    )

    indexer.build(
        embeddings
    )

    indexer.save()

    print()

    print("=" * 60)
    print("FAISS INDEX SAVED")
    print("=" * 60)

    new_indexer = FAISSIndexer(
        384
    )

    new_indexer.load()

    print()

    print("FAISS INDEX LOADED")

    print()

    print(
        "Vectors:",
        new_indexer.index.ntotal
    )


if __name__ == "__main__":
    main()