class ResultRanker:

    def rank(self, fused_results, documents):

        ranked_documents = []

        for rank, (doc_id, score) in enumerate(fused_results, start=1):

            document = next(
                doc
                for doc in documents
                if doc["id"] == doc_id
            )

            ranked_documents.append({

                "rank": rank,

                "id": doc_id,

                "score": score,

                "text": document["text"]

            })

        return ranked_documents