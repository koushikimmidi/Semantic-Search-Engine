from backend.embeddings.encoder import EmbeddingEncoder


def main():
    encoder = EmbeddingEncoder()

    sentences = [
        "Machine Learning is amazing.",
        "Artificial Intelligence is the future.",
        "Python is a programming language."
    ]

    embeddings = encoder.encode(sentences)

    print("Embedding Shape :", embeddings.shape)
    print()

    for i, vector in enumerate(embeddings):
        print(f"Sentence {i + 1}")
        print("Vector Length :", len(vector))
        print("First 10 Values :", vector[:10])
        print("-" * 60)


if __name__ == "__main__":
    main()