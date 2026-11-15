from backend.embeddings.encoder import EmbeddingEncoder


def main():

    print("Creating Encoder 1")

    encoder1 = EmbeddingEncoder()

    print("Creating Encoder 2")

    encoder2 = EmbeddingEncoder()

    print()

    print("Both encoders use the same model instance:")

    print(encoder1.model is encoder2.model)


if __name__ == "__main__":
    main()