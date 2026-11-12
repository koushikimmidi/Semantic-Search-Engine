from sentence_transformers import CrossEncoder


class CrossEncoderRanker:

    def __init__(self):

        self.model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )

    def score(self, query, documents):

        if not documents:
            return []

        pairs = [
            (query, document)
            for document in documents
        ]

        return self.model.predict(
            pairs
        )

    def rerank(self, query, documents):

        scores = self.score(
            query,
            documents
        )

        ranked = sorted(
            zip(documents, scores),
            key=lambda x: x[1],
            reverse=True
        )

        return ranked
