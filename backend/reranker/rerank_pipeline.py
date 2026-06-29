from backend.reranker import CrossEncoderRanker


class RerankPipeline:

    def __init__(self):

        self.cross_encoder = CrossEncoderRanker()

    def rerank(
        self,
        query,
        ranked_results
    ):

        documents = [

            result["text"]

            for result in ranked_results

        ]

        ranked = self.cross_encoder.rerank(

            query,

            documents

        )

        reranked = []

        for rank, (document, score) in enumerate(

            ranked,

            start=1

        ):

            for result in ranked_results:

                if result["text"] == document:

                    reranked.append(

                        {

                            "rank": rank,

                            "id": result["id"],

                            "text": document,

                            "cross_score": float(score)

                        }

                    )

                    break

        return reranked