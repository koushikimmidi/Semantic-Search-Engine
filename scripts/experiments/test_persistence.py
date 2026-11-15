import numpy as np

from backend.embeddings import FAISSIndexer
from backend.persistence import PersistenceManager


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

    manager = PersistenceManager()

    manager.save(
        embeddings,
        indexer
    )

    loaded = manager.load_embeddings()

    print()

    print("=" * 60)
    print("PERSISTENCE TEST")
    print("=" * 60)

    print()

    print("Embedding Shape:", loaded.shape)

    print("FAISS Saved Successfully")


if __name__ == "__main__":
    main()