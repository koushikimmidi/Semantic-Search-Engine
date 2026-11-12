import os
import re

from backend.llm import GemmaLLM
from backend.llm.gemma import FALLBACK_ANSWER
from backend.confidence.confidence_engine import ConfidenceEngine
from backend.automation.message_router import MessageRouter
from backend.intent.intent_detector import IntentDetector


_CITATION_MARKERS = re.compile(r"\s*\[\d+(?:\s*,\s*\d+)*\]")


def strip_citations(text):
    """
    Remove inline citation markers like [1] or [2, 3] (used when an
    answer is sent by email, where the sources are not shown).
    """

    if not text:
        return text

    text = _CITATION_MARKERS.sub("", text)

    return re.sub(r"\s+([.,;:!?])", r"\1", text).strip()


class RAGPipeline:

    def __init__(self, llm=None, intent_detector=None):

        self.llm = llm or GemmaLLM()

        self.confidence_engine = ConfidenceEngine()

        self.message_router = MessageRouter()

        self.intent_detector = intent_detector or IntentDetector()

        # Context budget: at most `max_sources` chunks and roughly
        # `max_context_chars` characters. Sources after the first
        # are only used when the reranker finds them relevant.
        self.max_sources = int(os.getenv("RAG_MAX_SOURCES", "4"))
        self.max_context_chars = int(os.getenv("RAG_MAX_CONTEXT_CHARS", "2400"))
        self.min_source_score = float(os.getenv("RAG_MIN_SOURCE_SCORE", "-2.0"))

    # ========================================================
    # CONTEXT
    # ========================================================

    def select_sources(self, search_results, top_k=None):

        limit = top_k or self.max_sources

        selected = []
        used_chars = 0

        for result in search_results:

            if len(selected) >= limit:
                break

            score = result.get("cross_score")

            if (
                selected
                and score is not None
                and score < self.min_source_score
            ):
                break

            length = len(result.get("text", ""))

            if selected and used_chars + length > self.max_context_chars:
                break

            selected.append(result)
            used_chars += length

        return selected

    def build_context(self, sources):

        blocks = []

        for number, result in enumerate(sources, start=1):

            label = result.get("source", "document")
            page = result.get("page")

            if page:
                label = f"{label}, page {page}"

            blocks.append(f"[{number}] ({label})\n{result.get('text', '')}")

        return "\n\n".join(blocks)

    def prepare(self, query, search_results, top_k=None):
        """
        Intent + selected sources + numbered context, before the LLM.
        """

        intent = self.intent_detector.detect(query)

        sources = self.select_sources(search_results or [], top_k)

        return intent, sources, self.build_context(sources)

    def finalize(self, query, answer, sources, intent):
        """
        Confidence + routing for a generated answer.
        """

        answer = (answer or "").strip() or FALLBACK_ANSWER

        confidence = self.confidence_engine.evaluate(
            answer,
            sources,
            intent
        )

        routing = self.message_router.route(confidence)

        return {
            "query": query,
            "intent": intent,
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "routing": routing
        }

    # ========================================================
    # ANSWER (blocking)
    # ========================================================

    def generate_answer(
        self,
        query,
        search_results,
        top_k=None
    ):

        intent, sources, context = self.prepare(query, search_results, top_k)

        # No evidence: skip the LLM call entirely.
        if not sources:
            answer = FALLBACK_ANSWER
        else:
            answer = self.llm.generate(query, context)

        return self.finalize(query, answer, sources, intent)

    # ========================================================
    # ANSWER (streaming)
    # ========================================================

    def stream_answer(self, query, search_results, top_k=None):
        """
        Yield events:
            {"type": "sources", "sources": [...], "intent": {...}}
            {"type": "token", "text": "..."}            (repeated)
            {"type": "done", ...full response...}
        """

        intent, sources, context = self.prepare(query, search_results, top_k)

        yield {
            "type": "sources",
            "query": query,
            "intent": intent,
            "sources": sources
        }

        parts = []

        if not sources:

            parts.append(FALLBACK_ANSWER)

            yield {"type": "token", "text": FALLBACK_ANSWER}

        else:

            for text in self.llm.generate_stream(query, context):

                parts.append(text)

                yield {"type": "token", "text": text}

        response = self.finalize(query, "".join(parts), sources, intent)
        response["type"] = "done"

        yield response
