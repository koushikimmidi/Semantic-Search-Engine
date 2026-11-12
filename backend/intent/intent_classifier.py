import json
import os
import threading

import numpy as np


DEFAULT_EXAMPLES_PATH = "data/intent/intent_examples.json"

# Label used in the training data for questions the knowledge base
# does not cover. It is reported to the rest of the system as UNKNOWN.
OUT_OF_SCOPE = "OUT_OF_SCOPE"


class IntentClassifier:
    """
    Few-shot intent classifier using sentence embeddings.

    Every labelled example is embedded once. A query is embedded and
    compared (cosine similarity) with all examples; each intent's
    score is the mean of its `top_k` most similar examples.

    The query is UNKNOWN when the best intent is OUT_OF_SCOPE or the
    best similarity is below `min_similarity`, and AMBIGUOUS when the
    top two intents are closer than `ambiguity_margin`.
    """

    def __init__(
        self,
        encoder=None,
        examples_path=None,
        top_k=3,
        min_similarity=0.35,
        ambiguity_margin=0.01
    ):

        self._encoder = encoder
        self.examples_path = examples_path or os.getenv(
            "INTENT_EXAMPLES_PATH",
            DEFAULT_EXAMPLES_PATH
        )
        self.top_k = top_k
        self.min_similarity = min_similarity
        self.ambiguity_margin = ambiguity_margin

        self._lock = threading.Lock()
        self._labels = None
        self._matrix = None

    # ========================================================
    # SETUP
    # ========================================================

    def _get_encoder(self):

        if self._encoder is None:
            # Reuse the already-loaded embedding model.
            from backend.cache import ModelCache
            self._encoder = ModelCache.get_model()

        return self._encoder

    def _encode(self, texts):

        # Any object with .encode(list_of_texts) -> 2D array works
        # (SentenceTransformer in production, a stub in tests).
        vectors = np.asarray(
            self._get_encoder().encode(texts),
            dtype="float32"
        )

        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0

        return vectors / norms

    def _ensure_ready(self):

        if self._matrix is not None:
            return

        with self._lock:

            if self._matrix is not None:
                return

            with open(self.examples_path, "r", encoding="utf-8") as file:
                examples = json.load(file)

            labels = []
            texts = []

            for label, items in examples.items():
                for text in items:
                    labels.append(label)
                    texts.append(text)

            if not texts:
                raise ValueError("No intent examples were found.")

            self._matrix = self._encode(texts)
            self._labels = np.array(labels)

    # ========================================================
    # PREDICT
    # ========================================================

    def scores(self, query):
        """
        Return {intent: score} sorted from best to worst.
        """

        self._ensure_ready()

        query_vector = self._encode([query])[0]

        similarities = self._matrix @ query_vector

        result = {}

        for label in dict.fromkeys(self._labels):

            label_sims = np.sort(similarities[self._labels == label])[::-1]

            result[str(label)] = float(np.mean(label_sims[:self.top_k]))

        return dict(
            sorted(result.items(), key=lambda item: item[1], reverse=True)
        )

    def predict(self, query):

        if not query or not query.strip():
            return {
                "intent": "UNKNOWN",
                "confidence": 0.0,
                "scores": {}
            }

        scores = self.scores(query)
        ranked = list(scores.items())

        best_label, best_score = ranked[0]
        best_label = str(best_label)
        second_label, second_score = (
            ranked[1] if len(ranked) > 1 else (None, 0.0)
        )

        rounded = {k: round(v, 4) for k, v in scores.items()}

        if best_label == OUT_OF_SCOPE or best_score < self.min_similarity:

            return {
                "intent": "UNKNOWN",
                "confidence": 0.0,
                "similarity": round(best_score, 4),
                "scores": rounded
            }

        if (
            second_label not in (None, OUT_OF_SCOPE)
            and best_score - second_score < self.ambiguity_margin
        ):

            return {
                "intent": "AMBIGUOUS",
                "confidence": 0.0,
                "candidate_intents": [best_label, str(second_label)],
                "similarity": round(best_score, 4),
                "scores": rounded
            }

        # Map similarity and margin to a 0..1 confidence.
        strength = min(1.0, max(0.0, (best_score - self.min_similarity) / 0.35))
        margin = min(1.0, (best_score - second_score) / 0.15)

        confidence = round(0.5 + 0.5 * (0.6 * strength + 0.4 * margin), 2)

        return {
            "intent": best_label,
            "confidence": confidence,
            "similarity": round(best_score, 4),
            "scores": rounded
        }
