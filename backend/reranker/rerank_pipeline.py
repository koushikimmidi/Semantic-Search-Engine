from backend.reranker.cross_encoder import CrossEncoderRanker


class RerankPipeline:

    def __init__(self):

        self.cross_encoder = CrossEncoderRanker()

    def rerank(
        self,
        query,
        ranked_results
    ):

        if not ranked_results:
            return []

        documents = [
            result["text"]
            for result in ranked_results
        ]

        scores = self.cross_encoder.score(
            query,
            documents
        )

        # Pair each score with its own result (by position), so
        # chunks with identical text are never merged or dropped.
        scored = sorted(
            zip(ranked_results, scores),
            key=lambda item: item[1],
            reverse=True
        )

        reranked = []

        for rank, (result, score) in enumerate(scored, start=1):

            res_copy = result.copy()

            res_copy["rank"] = rank

            res_copy["cross_score"] = float(score)

            reranked.append(res_copy)

        return reranked
