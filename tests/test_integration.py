"""
Integration tests with the real models and knowledge base.

Skipped by default (they download models and take a minute):

    RUN_INTEGRATION=1 pytest tests/test_integration.py

Ollama is not required: the LLM is replaced with a fake, so these
tests check retrieval, reranking and routing on real data.
"""

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="set RUN_INTEGRATION=1 to run integration tests"
)


@pytest.fixture(scope="module")
def engine(tmp_path_factory):

    os.environ["EMBEDDING_CACHE_PATH"] = str(
        tmp_path_factory.mktemp("cache") / "embedding_cache.pkl"
    )

    from backend.engine.search_engine import SearchEngine

    search_engine = SearchEngine("data/documents/education")
    search_engine.load()

    return search_engine


@pytest.mark.parametrize("query, expected_source", [
    ("How many days do I have to ask for a refund?", "policies/refund_policy.pdf"),
    ("Which situations make a course non-refundable?", "policies/refund_policy.pdf"),
    ("What will I build in the Python Basics course?", "course_materials/python_basics.pdf"),
])
def test_top_result_comes_from_expected_document(engine, query, expected_source):

    results = engine.search(query)

    assert results[0]["source"] == expected_source


def test_off_topic_question_scores_far_below_auto_reply(engine):

    from backend.confidence.confidence_engine import ConfidenceEngine

    results = engine.search("What is the capital of Australia?")

    assert results[0]["cross_score"] < ConfidenceEngine().medium_threshold
