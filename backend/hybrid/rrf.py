class ReciprocalRankFusion:
    """
    Combines multiple ranked lists using Reciprocal Rank Fusion.
    """

    def __init__(self, k=60):
        self.k = k

    def fuse(self, ranked_lists):
        """
        ranked_lists:
        [
            [doc1, doc2, doc3],
            [doc2, doc1, doc4]
        ]
        """

        scores = {}

        for ranking in ranked_lists:

            for rank, doc_id in enumerate(ranking, start=1):

                score = 1 / (self.k + rank)

                scores[doc_id] = scores.get(doc_id, 0) + score

        final_results = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return final_results