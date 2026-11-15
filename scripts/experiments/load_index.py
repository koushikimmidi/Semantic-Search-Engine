from backend.embeddings.storage import IndexStorage


def main():

    index = IndexStorage.load(
        "data/index/faiss.index"
    )

    print()

    print("FAISS Index Loaded Successfully!")

    print(f"Total Documents : {index.ntotal}")

    print(f"Embedding Dimension : {index.d}")


if __name__ == "__main__":
    main()