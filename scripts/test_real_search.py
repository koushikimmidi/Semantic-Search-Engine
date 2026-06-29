from backend.preprocessing.loader import DataLoader
from backend.embeddings.encoder import EmbeddingEncoder
from backend.embeddings.indexer import FAISSIndexer
from backend.embeddings.search import SemanticSearcher


def main():

    loader = DataLoader("data/raw/sample_documents.json")

    documents = loader.load_documents()

    texts = [doc["text"] for doc in documents]

    encoder = EmbeddingEncoder()

    embeddings = encoder.encode(texts)

    indexer = FAISSIndexer(embeddings.shape[1])

    indexer.build(embeddings)

    searcher = SemanticSearcher(
        encoder,
        indexer.index
    )

    query = input("Enter your query : ")

    distances, indices = searcher.search(
        query,
        top_k=min(5, len(documents))
    )

    print("\nSemantic Search Results\n")

    for rank, (distance, index) in enumerate(zip(distances, indices), start=1):

        print(f"Rank : {rank}")
        print(f"Document ID : {documents[index]['id']}")
        print(f"Distance : {distance:.4f}")
        print(f"Text : {documents[index]['text']}")
        print("-" * 60)


if __name__ == "__main__":
    main()