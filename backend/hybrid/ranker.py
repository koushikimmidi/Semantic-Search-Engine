class ResultRanker:

    def rank(self, fused_results, documents):

        ranked_documents = []

        for rank, (doc_id, score) in enumerate(fused_results, start=1):

            document = next(
                doc
                for doc in documents
                if doc["id"] == doc_id
            )

            doc_copy = document.copy()

            doc_copy["rank"] = rank

            doc_copy["score"] = score

            ranked_documents.append(doc_copy)

        return ranked_documents