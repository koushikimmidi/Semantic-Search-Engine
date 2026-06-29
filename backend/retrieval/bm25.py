from rank_bm25 import BM25Okapi


class BM25Retriever:

    def __init__(self, tokenized_documents):
        self.bm25 = BM25Okapi(tokenized_documents)

    def search(self, query_tokens, top_k=5):
        scores = self.bm25.get_scores(query_tokens)

        ranked = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True
        )

        return ranked[:top_k]