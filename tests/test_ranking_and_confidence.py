import numpy as np

from backend.hybrid.rrf import ReciprocalRankFusion
from backend.reranker.rerank_pipeline import RerankPipeline
from backend.confidence.confidence_engine import ConfidenceEngine
from backend.embeddings.chunk_embedding_cache import ChunkEmbeddingCache

from tests.conftest import HashingEncoder


def test_rrf_rewards_documents_ranked_high_in_both_lists():

    fused = ReciprocalRankFusion().fuse([[1, 2, 3], [2, 1, 4]])

    ids = [doc_id for doc_id, _ in fused]

    assert set(ids[:2]) == {1, 2}
    assert ids[-1] in (3, 4)


def test_rerank_keeps_duplicate_texts_separate():

    class FakeCrossEncoder:
        def score(self, query, documents):
            return [1.0, 3.0, 2.0]

    pipeline = RerankPipeline.__new__(RerankPipeline)
    pipeline.cross_encoder = FakeCrossEncoder()

    results = [
        {"id": 1, "text": "same text"},
        {"id": 2, "text": "same text"},
        {"id": 3, "text": "other"}
    ]

    reranked = pipeline.rerank("q", results)

    assert [r["id"] for r in reranked] == [2, 3, 1]
    assert [r["rank"] for r in reranked] == [1, 2, 3]
    assert pipeline.rerank("q", []) == []


def _results(*scores, text="refund policy text", source="policies/refund_policy.pdf"):

    return [
        {"text": text, "source": source, "cross_score": s}
        for s in scores
    ]


def test_confidence_auto_reply_on_strong_evidence():

    engine = ConfidenceEngine(very_high_threshold=3.0, high_threshold=0.5)

    result = engine.evaluate(
        "The refund period is 7 days [1].",
        _results(4.0, 1.0),
        {"intent": "REFUND", "confidence": 1.0}
    )

    assert result["decision"] == "AUTO_REPLY"


def test_confidence_blocks_fallback_answer_and_weak_evidence():

    engine = ConfidenceEngine(very_high_threshold=3.0, high_threshold=0.5, medium_threshold=-3.0)

    fallback = engine.evaluate(
        "I cannot answer this based on the provided documents.",
        _results(6.0)
    )
    weak = engine.evaluate("Some answer.", _results(-8.0, -9.0))

    assert fallback["decision"] == "HUMAN_REVIEW"
    assert weak["decision"] == "HUMAN_REVIEW"
    assert weak["level"] == "LOW"


def test_confidence_intent_gate_blocks_mismatched_evidence():

    engine = ConfidenceEngine(very_high_threshold=3.0)

    result = engine.evaluate(
        "Answer [1].",
        _results(9.0, text="python lists and tuples", source="course_materials/python_basics.pdf"),
        {"intent": "REFUND", "confidence": 1.0}
    )

    assert result["decision"] == "HUMAN_REVIEW"


def test_confidence_thresholds_from_environment(monkeypatch):

    monkeypatch.setenv("CONFIDENCE_VERY_HIGH_THRESHOLD", "7.5")

    assert ConfidenceEngine().very_high_threshold == 7.5


def test_embedding_cache_encodes_only_new_texts(tmp_path):

    encoder = HashingEncoder()
    cache_file = tmp_path / "cache.pkl"

    cache = ChunkEmbeddingCache("model-a", cache_file=str(cache_file))
    first = cache.encode(["alpha text", "beta text"], encoder.encode)

    assert cache.last_misses == 2

    # New instance reads from disk; only the new text is encoded.
    cache = ChunkEmbeddingCache("model-a", cache_file=str(cache_file))
    second = cache.encode(["alpha text", "beta text", "gamma"], encoder.encode)

    assert cache.last_hits == 2 and cache.last_misses == 1
    assert np.allclose(first, second[:2])

    # A different model never reuses vectors.
    other = ChunkEmbeddingCache("model-b", cache_file=str(cache_file))
    other.encode(["alpha text"], encoder.encode)

    assert other.last_misses == 1


def test_embedding_cache_survives_corrupt_file(tmp_path):

    cache_file = tmp_path / "cache.pkl"
    cache_file.write_bytes(b"not a pickle")

    cache = ChunkEmbeddingCache("model", cache_file=str(cache_file))

    assert cache.encode(["x"], HashingEncoder().encode).shape[0] == 1
