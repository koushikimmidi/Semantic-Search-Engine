from backend.preprocessing.pipeline import PreprocessingPipeline
from backend.preprocessing.cleaner import TextCleaner
from backend.preprocessing.tokenizer import Tokenizer
from backend.retrieval.bm25 import BM25Retriever


def main():
    # Load and preprocess documents
    pipeline = PreprocessingPipeline("data/raw/sample_documents.json")
    documents = pipeline.process()

    # Extract tokenized documents
    tokenized_docs = [doc["tokens"] for doc in documents]

    # Build BM25 index
    retriever = BM25Retriever(tokenized_docs)

    # Prepare query
    cleaner = TextCleaner()
    tokenizer = Tokenizer()

    query = "machine learning"
    query = cleaner.clean(query)
    query_tokens = tokenizer.tokenize(query)

    # Search
    results = retriever.search(query_tokens)

    print("\n========== SEARCH RESULTS ==========\n")

    for index, score in results:
        print(f"Document ID : {documents[index]['id']}")
        print(f"Score       : {score:.4f}")
        print(f"Text        : {documents[index]['text']}")
        print("-" * 50)


if __name__ == "__main__":
    main()