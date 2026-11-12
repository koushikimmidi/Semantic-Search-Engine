import os


def _env_float(name, default):

    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return float(default)


class ConfidenceEngine:
    """
    Decides AUTO_REPLY vs HUMAN_REVIEW from cross-encoder scores
    (ms-marco logits), the LLM answer, and intent/evidence agreement.

    Thresholds are tuned with `python -m scripts.evaluate_pipeline`
    and can be overridden with CONFIDENCE_* environment variables.

    Tuning (Nov 2026, eval_set.json, reranking on the original
    question): the highest-scoring unanswerable question scored
    -3.1, so auto replies need >= 3.0, or >= 0.5 with a clear lead
    (gap >= 0.5) over the next source. Below -3.0 evidence is LOW.
    """

    def __init__(
        self,
        high_threshold=None,
        very_high_threshold=None,
        medium_threshold=None,
        minimum_score_gap=None
    ):

        self.high_threshold = (
            high_threshold if high_threshold is not None
            else _env_float("CONFIDENCE_HIGH_THRESHOLD", 0.5)
        )
        self.very_high_threshold = (
            very_high_threshold if very_high_threshold is not None
            else _env_float("CONFIDENCE_VERY_HIGH_THRESHOLD", 3.0)
        )
        self.medium_threshold = (
            medium_threshold if medium_threshold is not None
            else _env_float("CONFIDENCE_MEDIUM_THRESHOLD", -3.0)
        )
        self.minimum_score_gap = (
            minimum_score_gap if minimum_score_gap is not None
            else _env_float("CONFIDENCE_MIN_SCORE_GAP", 0.5)
        )

        # ----------------------------------------------------
        # Intent → Evidence keywords
        #
        # These are used as an additional safety signal.
        # They do NOT replace semantic retrieval.
        # ----------------------------------------------------

        self.intent_keywords = {

            "REFUND": [
                "refund",
                "refundable",
                "refund period",
                "refund policy"
            ],

            "PASSWORD_RESET": [
                "password",
                "reset password",
                "forgot password",
                "password reset"
            ],

            "COURSE_ACCESS": [
                "course access",
                "access course",
                "course",
                "enrollment"
            ],

            "ACCOUNT_LOGIN": [
                "login",
                "log in",
                "account",
                "sign in"
            ],

            "CERTIFICATE": [
                "certificate",
                "certification",
                "download certificate"
            ],

            "PAYMENT": [
                "payment",
                "payment failed",
                "transaction",
                "billing"
            ],

            "CANCELLATION": [
                "cancel",
                "cancellation",
                "cancel course"
            ],

            "TECHNICAL_SUPPORT": [
                "technical",
                "error",
                "video",
                "not playing",
                "not loading",
                "website",
                "bug",
                "problem"
            ],

            "GENERAL_FAQ": [
                "faq",
                "information",
                "course information",
                "general"
            ]
        }

    # ========================================================
    # INTENT COMPATIBILITY
    # ========================================================

    def _check_intent_compatibility(
        self,
        intent_result,
        search_results
    ):

        # ----------------------------------------------------
        # No intent information
        # ----------------------------------------------------

        if not intent_result:

            return {
                "compatible": True,
                "score": 1.0,
                "supporting_results": 0,
                "reason": "No intent information was provided."
            }

        intent = intent_result.get(
            "intent",
            "UNKNOWN"
        )

        intent_confidence = float(
            intent_result.get(
                "confidence",
                0.0
            )
        )

        # ----------------------------------------------------
        # Unknown intent
        #
        # Do not punish retrieval when the intent detector
        # cannot determine the user's intent.
        # ----------------------------------------------------

        if intent == "UNKNOWN":

            return {
                "compatible": True,
                "score": 1.0,
                "supporting_results": 0,
                "reason": "Intent could not be determined."
            }

        # ----------------------------------------------------
        # Ambiguous intent
        #
        # Do not automatically reject the evidence.
        # The normal confidence rules will still apply.
        # ----------------------------------------------------

        if intent == "AMBIGUOUS":

            return {
                "compatible": True,
                "score": 0.5,
                "supporting_results": 0,
                "reason": "The detected intent is ambiguous."
            }

        # ----------------------------------------------------
        # Get keywords for detected intent
        # ----------------------------------------------------

        keywords = self.intent_keywords.get(
            intent,
            []
        )

        if not keywords:

            return {
                "compatible": True,
                "score": 1.0,
                "supporting_results": 0,
                "reason": (
                    "No specific evidence keywords are "
                    "configured for this intent."
                )
            }

        # ----------------------------------------------------
        # Check retrieved evidence
        # ----------------------------------------------------

        supporting_results = 0

        for result in search_results:

            text = result.get(
                "text",
                ""
            ).lower()

            source = result.get(
                "source",
                ""
            ).lower()

            combined_text = (
                text
                + " "
                + source
            )

            matched = False

            for keyword in keywords:

                if keyword.lower() in combined_text:

                    matched = True
                    break

            if matched:

                supporting_results += 1

        # ----------------------------------------------------
        # Calculate compatibility score
        # ----------------------------------------------------

        total_results = len(
            search_results
        )

        if total_results == 0:

            compatibility_score = 0.0

        else:

            compatibility_score = (
                supporting_results
                / total_results
            )

        # ----------------------------------------------------
        # Determine compatibility
        # ----------------------------------------------------

        compatible = (
            supporting_results >= 1
        )

        # ----------------------------------------------------
        # Explanation
        # ----------------------------------------------------

        if compatible:

            reason = (
                f"Retrieved evidence is compatible "
                f"with the detected intent '{intent}'."
            )

        else:

            reason = (
                f"Retrieved evidence does not strongly "
                f"match the detected intent '{intent}'."
            )

        return {

            "compatible": compatible,

            "score": round(
                compatibility_score,
                4
            ),

            "supporting_results": (
                supporting_results
            ),

            "intent": intent,

            "intent_confidence": (
                intent_confidence
            ),

            "reason": reason

        }

    # ========================================================
    # CONFIDENCE EVALUATION
    # ========================================================

    def evaluate(
        self,
        answer,
        search_results,
        intent_result=None
    ):

        # ----------------------------------------------------
        # Basic validation
        # ----------------------------------------------------

        if not search_results:

            return {
                "confidence": 0.0,
                "level": "LOW",
                "decision": "HUMAN_REVIEW",
                "reason": "No search results were found."
            }

        # ----------------------------------------------------
        # Check fallback answer
        # ----------------------------------------------------

        fallback_message = (
            "I cannot answer this based on the provided documents."
        )

        if (
            not answer
            or fallback_message.lower()
            in answer.lower()
        ):

            return {
                "confidence": 0.0,
                "level": "LOW",
                "decision": "HUMAN_REVIEW",
                "reason": (
                    "The answer is not supported by "
                    "the available documents."
                )
            }

        # ----------------------------------------------------
        # Intent compatibility
        # ----------------------------------------------------

        intent_check = (
            self._check_intent_compatibility(
                intent_result,
                search_results
            )
        )

        # ----------------------------------------------------
        # Extract cross-encoder scores
        # ----------------------------------------------------

        scores = []

        for result in search_results:

            score = result.get(
                "cross_score"
            )

            if score is not None:

                scores.append(
                    float(score)
                )

        # ----------------------------------------------------
        # Validate scores
        # ----------------------------------------------------

        if not scores:

            return {
                "confidence": 0.0,
                "level": "LOW",
                "decision": "HUMAN_REVIEW",
                "reason": (
                    "No reranker scores are available."
                ),
                "intent": intent_check
            }

        # ----------------------------------------------------
        # Sort scores
        # ----------------------------------------------------

        sorted_scores = sorted(
            scores,
            reverse=True
        )

        # ----------------------------------------------------
        # Top score
        # ----------------------------------------------------

        top_score = sorted_scores[0]

        # ----------------------------------------------------
        # Score gap
        # ----------------------------------------------------

        if len(sorted_scores) >= 2:

            score_gap = (
                sorted_scores[0]
                - sorted_scores[1]
            )

        else:

            score_gap = 0.0

        # ----------------------------------------------------
        # Count supporting evidence
        # ----------------------------------------------------

        supporting_results = sum(

            1

            for score in scores

            if score >= self.medium_threshold

        )

        # ====================================================
        # INTENT SAFETY GATE
        #
        # If the detected intent is known and the retrieved
        # evidence does not match it, automatic reply is
        # blocked.
        # ====================================================

        known_intent = (
            intent_result is not None
            and intent_result.get(
                "intent",
                "UNKNOWN"
            ) not in (
                "UNKNOWN",
                "AMBIGUOUS"
            )
        )

        if (
            known_intent
            and not intent_check["compatible"]
        ):

            return {

                "confidence": 0.0,

                "level": "LOW",

                "decision": "HUMAN_REVIEW",

                "reason": (
                    "Intent and retrieved evidence "
                    "are not sufficiently compatible. "
                    "Automatic reply is blocked."
                ),

                "top_score": round(
                    top_score,
                    4
                ),

                "score_gap": round(
                    score_gap,
                    4
                ),

                "supporting_results": (
                    supporting_results
                ),

                "intent": intent_check

            }

        # ====================================================
        # VERY HIGH confidence
        # ====================================================

        if (
            top_score >= self.very_high_threshold
            and supporting_results >= 1
        ):

            return {

                "confidence": 1.0,

                "level": "HIGH",

                "decision": "AUTO_REPLY",

                "reason": (
                    "Very strong reranker evidence "
                    "supports the answer and the "
                    "retrieved evidence is compatible "
                    "with the detected intent."
                ),

                "top_score": round(
                    top_score,
                    4
                ),

                "score_gap": round(
                    score_gap,
                    4
                ),

                "supporting_results": (
                    supporting_results
                ),

                "intent": intent_check

            }

        # ====================================================
        # HIGH confidence
        # ====================================================

        if (
            top_score >= self.high_threshold
            and score_gap >= self.minimum_score_gap
        ):

            return {

                "confidence": 1.0,

                "level": "HIGH",

                "decision": "AUTO_REPLY",

                "reason": (
                    "Strong reranker evidence supports "
                    "the answer and the retrieved evidence "
                    "is compatible with the detected intent."
                ),

                "top_score": round(
                    top_score,
                    4
                ),

                "score_gap": round(
                    score_gap,
                    4
                ),

                "supporting_results": (
                    supporting_results
                ),

                "intent": intent_check

            }

        # ====================================================
        # MEDIUM confidence
        # ====================================================

        if (
            top_score >= self.medium_threshold
        ):

            return {

                "confidence": 0.5,

                "level": "MEDIUM",

                "decision": "HUMAN_REVIEW",

                "reason": (
                    "Relevant evidence exists, but "
                    "confidence is not strong enough "
                    "for automatic reply."
                ),

                "top_score": round(
                    top_score,
                    4
                ),

                "score_gap": round(
                    score_gap,
                    4
                ),

                "supporting_results": (
                    supporting_results
                ),

                "intent": intent_check

            }

        # ====================================================
        # LOW confidence
        # ====================================================

        return {

            "confidence": 0.0,

            "level": "LOW",

            "decision": "HUMAN_REVIEW",

            "reason": (
                "The retrieved evidence is weak."
            ),

            "top_score": round(
                top_score,
                4
            ),

            "score_gap": round(
                score_gap,
                4
            ),

            "supporting_results": (
                supporting_results
            ),

            "intent": intent_check

        }