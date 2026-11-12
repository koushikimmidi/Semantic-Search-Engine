"""
Shared fixtures.

Unit tests never load the real embedding / cross-encoder models or
call Ollama: lightweight fakes stand in for them, so the suite runs
in seconds and works in CI without a GPU or an LLM.

Set RUN_INTEGRATION=1 to also run tests/test_integration.py, which
uses the real models and the real knowledge base.
"""

import hashlib
import importlib
import os
import re
import sys

import numpy as np
import pytest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# FAKES
# ============================================================

class HashingEncoder:
    """
    Deterministic bag-of-words "embedding": texts sharing words get
    similar vectors. Enough to test classifier/caching logic.
    """

    def __init__(self, dimension=256):
        self.dimension = dimension
        self.calls = 0

    def encode(self, texts, **kwargs):
        self.calls += 1
        vectors = np.zeros((len(texts), self.dimension), dtype="float32")
        for row, text in enumerate(texts):
            for word in re.findall(r"[a-z0-9]+", text.lower()):
                digest = int(hashlib.md5(word.encode()).hexdigest(), 16)
                vectors[row, digest % self.dimension] += 1.0
        return vectors


class FakeLLM:
    """Echoes the first source as the answer, with a citation."""

    def __init__(self, answer=None):
        self.answer = answer
        self.calls = 0

    def _answer(self, context):
        if self.answer is not None:
            return self.answer
        match = re.search(r"\[1\] \([^)]*\)\n(.+)", context)
        first = match.group(1) if match else "No context."
        return f"{first[:80]} [1]"

    def generate(self, query, context):
        self.calls += 1
        return self._answer(context)

    def generate_stream(self, query, context):
        self.calls += 1
        text = self._answer(context)
        for start in range(0, len(text), 10):
            yield text[start:start + 10]


class FakeSearchEngine:
    """
    Loads the knowledge base with the real DocumentIndexer and ranks
    chunks by word overlap. `cross_score` mimics the reranker: high
    for strong overlap, very negative for none.
    """

    def __init__(self, data_path):
        self.data_path = data_path
        self.processed_docs = []
        self.documents = []
        self.loads = 0

    def load(self):
        from backend.indexing import DocumentIndexer
        self.processed_docs = DocumentIndexer().index_folder(self.data_path)
        self.documents = [doc["text"] for doc in self.processed_docs]
        self.loads += 1

    def search(self, query, **kwargs):
        words = set(re.findall(r"[a-z]{3,}", (query or "").lower()))
        if not words:
            return []
        scored = []
        for doc in self.processed_docs:
            doc_words = set(re.findall(r"[a-z]{3,}", doc["text"].lower()))
            overlap = len(words & doc_words)
            result = dict(doc)
            result["cross_score"] = float(overlap * 2.5 - 1) if overlap else -11.0
            scored.append(result)
        scored.sort(key=lambda r: r["cross_score"], reverse=True)
        return scored[:10]


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def knowledge_base(tmp_path):
    """A tiny knowledge base folder with two documents."""

    kb = tmp_path / "kb"
    (kb / "policies").mkdir(parents=True)

    (kb / "policies" / "refund_policy.txt").write_text(
        "Refund Policy\n"
        "Refund Eligibility\n"
        "Students may request a full refund within 7 calendar days "
        "of enrollment. The course must not have been completed.\n",
        encoding="utf-8"
    )

    (kb / "password_reset.md").write_text(
        "# Password Reset\n\n"
        "Use the password reset option on the login page. "
        "Check your spam folder if the reset email does not arrive.\n",
        encoding="utf-8"
    )

    return kb


@pytest.fixture
def api(monkeypatch, tmp_path, knowledge_base):
    """
    A TestClient for the FastAPI app wired to fakes and temporary
    folders. Authentication is enabled with known keys.
    """

    data_dir = tmp_path / "automation"

    monkeypatch.setenv("KNOWLEDGE_BASE_PATH", str(knowledge_base))
    monkeypatch.setenv("AUTOMATION_DATA_DIR", str(data_dir))
    monkeypatch.setenv("ADMIN_API_KEY", "admin-test-key")
    monkeypatch.setenv("AGENT_API_KEY", "agent-test-key")
    monkeypatch.setenv("AUTOMATION_SEND_EMAILS", "false")
    monkeypatch.setenv("EMAIL_HOST", "")
    monkeypatch.setenv("EMAIL_USERNAME", "")
    monkeypatch.setenv("EMAIL_PASSWORD", "")
    monkeypatch.setenv("SMTP_USERNAME", "")
    monkeypatch.setenv("SMTP_PASSWORD", "")

    import backend.engine.search_engine as search_engine_module
    import backend.rag as rag_module
    from backend.rag.rag_pipeline import RAGPipeline
    from backend.intent.intent_detector import IntentDetector

    def make_rag():
        return RAGPipeline(
            llm=FakeLLM(),
            intent_detector=IntentDetector(use_classifier=False)
        )

    monkeypatch.setattr(search_engine_module, "SearchEngine", FakeSearchEngine)
    monkeypatch.setattr(rag_module, "RAGPipeline", make_rag)

    sys.modules.pop("backend.api.app", None)
    app_module = importlib.import_module("backend.api.app")

    from fastapi.testclient import TestClient

    client = TestClient(app_module.app)
    client.app_module = app_module

    yield client

    sys.modules.pop("backend.api.app", None)


ADMIN = {"X-API-Key": "admin-test-key"}
AGENT = {"X-API-Key": "agent-test-key"}
