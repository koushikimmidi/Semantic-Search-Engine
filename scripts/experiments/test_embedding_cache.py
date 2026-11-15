import numpy as np

from backend.embeddings import EmbeddingCache


def main():

    embeddings = np.random.rand(
        5,
        384
    ).astype("float32")

    cache = EmbeddingCache()

    cache.save(
        embeddings
    )

    print()
    print("=" * 60)
    print("EMBEDDINGS SAVED")
    print("=" * 60)

    loaded = cache.load()

    print()
    print("Loaded Shape :", loaded.shape)
    print("First Vector :", loaded[0][:5])


if __name__ == "__main__":
    main()