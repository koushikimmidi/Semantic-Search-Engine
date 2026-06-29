from backend.hybrid.rrf import ReciprocalRankFusion
from backend.hybrid.ranker import ResultRanker


class HybridSearch:
    """
    Hybrid Search using BM25 + Dense Retrieval + RRF.
    """

    def __init__(self, bm25, dense):
        self.bm25 = bm25
        self.dense = dense
        self.rrf = ReciprocalRankFusion()
        self.ranker = ResultRanker()

    def search(self, bm25_ids, dense_ids, documents):
        """
        Combine BM25 and Dense rankings using RRF
        and return ranked documents.
        """

        fused = self.rrf.fuse(
            [
                bm25_ids,
                dense_ids
            ]
        )

        ranked_documents = self.ranker.rank(
            fused,
            documents
        )

        return ranked_documents