import numpy as np

from backend.embeddings import (
    FAISSIndexer,
    IndexPersistence
)


def main():

    vectors = np.random.rand(
        5,
        384
    ).astype("float32")

    indexer = FAISSIndexer(384)

    indexer.build(vectors)

    persistence = IndexPersistence()

    persistence.save(
        indexer.index,
        [
            "Doc A",
            "Doc B",
            "Doc C",
            "Doc D",
            "Doc E"
        ]
    )

    print()

    print("Index Saved Successfully")

    index, docs = persistence.load()

    print()

    print("Index Loaded Successfully")

    print()

    print("Documents")

    for document in docs:

        print(document)


if __name__ == "__main__":
    main()