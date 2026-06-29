from backend.ingestion import IngestionPipeline


def main():

    pipeline = IngestionPipeline()

    result = pipeline.build(
        "data/documents"
    )

    if result is None:
        return

    print()

    print("=" * 60)
    print("DOCUMENTS")
    print("=" * 60)

    for document in result["documents"]:

        print()

        print(document)


if __name__ == "__main__":
    main()