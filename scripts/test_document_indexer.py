from backend.indexing import DocumentIndexer


def main():

    indexer = DocumentIndexer()

    documents = indexer.index_folder(
        "data/documents"
    )

    print()

    print("=" * 60)
    print("INDEXED DOCUMENTS")
    print("=" * 60)

    for document in documents:

        print()

        print(document)


if __name__ == "__main__":
    main()