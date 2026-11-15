from backend.loaders.txt_loader import TXTLoader


def main():

    loader = TXTLoader()

    text = loader.load(
        "data/documents/sample.txt"
    )

    print()

    print("=" * 60)
    print("TXT CONTENT")
    print("=" * 60)

    print(text)


if __name__ == "__main__":
    main()