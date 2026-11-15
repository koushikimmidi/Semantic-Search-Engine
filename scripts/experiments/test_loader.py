from backend.preprocessing.loader import DataLoader


def main():
    loader = DataLoader("data/raw/sample_documents.json")

    documents = loader.load_documents()

    print(documents)


if __name__ == "__main__":
    main()