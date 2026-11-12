import os
import re


class IntentDetector:
    """
    Hybrid intent detection.

    1. Rules: exact support phrases ("forgot my password"). Very
       precise, but only fire on phrasings they list.
    2. Classifier: few-shot embedding classifier trained on
       data/intent/intent_examples.json. Handles new phrasings.

    A specific rule match wins (confirmed by the classifier when
    both agree). The classifier decides when rules find nothing or
    are ambiguous. If the classifier is unavailable, rules alone are
    used, so detection never fails.
    """

    def __init__(self, classifier=None, use_classifier=None):

        if use_classifier is None:
            use_classifier = (
                os.getenv("INTENT_CLASSIFIER", "true").strip().lower()
                not in ("0", "false", "no", "off")
            )

        self.use_classifier = use_classifier
        self._classifier = classifier

        self.intent_patterns = {

            "PASSWORD_RESET": [
                "reset password",
                "reset my password",
                "forgot password",
                "forgot my password",
                "forgotten password",
                "change password",
                "change my password",
                "new password",
                "password reset",
                "password recovery",
                "recover my password"
            ],

            "ACCOUNT_LOGIN": [
                "cannot login",
                "can't login",
                "cannot log in",
                "can't log in",
                "unable to login",
                "unable to log in",
                "login issue",
                "login problem",
                "login error",
                "account access",
                "cannot access my account",
                "can't access my account",
                "unable to access my account"
            ],

            "REFUND": [
                "refund",
                "get my money back",
                "money back",
                "refund request",
                "request a refund",
                "want a refund",
                "need a refund"
            ],

            "CANCELLATION": [
                "cancel course",
                "cancel my course",
                "course cancellation",
                "cancel enrollment",
                "cancel my enrollment",
                "cancellation request",
                "withdraw from course"
            ],

            "PAYMENT": [
                "payment",
                "payment failed",
                "payment issue",
                "payment problem",
                "transaction failed",
                "transaction issue",
                "charged",
                "billing",
                "invoice",
                "upi payment"
            ],

            "COURSE_ACCESS": [
                "cannot access course",
                "can't access course",
                "course access",
                "access my course",
                "course not opening",
                "course unavailable",
                "cannot open course",
                "can't open course",
                "course access issue",
                "unable to access course"
            ],

            "CERTIFICATE": [
                "certificate",
                "course certificate",
                "completion certificate",
                "certificate not received",
                "certificate download",
                "download certificate",
                "download my certificate",
                "get my certificate",
                "receive my certificate"
            ],

            "TECHNICAL_SUPPORT": [
                "technical issue",
                "technical problem",
                "website issue",
                "website problem",
                "platform issue",
                "platform problem",

                "video not playing",
                "video is not playing",
                "video isn't playing",
                "video is not working",
                "video not working",
                "video playback",
                "video playback issue",
                "video playback problem",
                "video issue",
                "video problem",

                "page not loading",
                "page is not loading",
                "website not loading",
                "website is not loading",

                "error message",
                "system error",
                "application error",
                "bug"
            ],

            "COURSE_INFORMATION": [
                "course information",
                "course details",
                "course syllabus",
                "course duration",
                "course modules",
                "course content",
                "course prerequisites",
                "learning outcomes",
                "what is this course",
                "tell me about the course",
                "information about the course"
            ],

            "GENERAL_FAQ": [
                "faq",
                "frequently asked questions",
                "frequently asked",
                "how does the platform work",
                "how does the academy work",
                "general information",
                "general question"
            ]
        }

    # ========================================================
    # TEXT NORMALIZATION
    # ========================================================

    def _normalize(
        self,
        text
    ):

        text = text.lower().strip()

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text

    # ========================================================
    # INTENT DETECTION
    # ========================================================

    def detect_rules(
        self,
        query
    ):

        if not query or not query.strip():

            return {
                "intent": "UNKNOWN",
                "confidence": 0.0,
                "matched_patterns": []
            }

        normalized_query = self._normalize(
            query
        )

        matches = {}

        # ----------------------------------------------------
        # Find matching intent patterns
        # ----------------------------------------------------

        for intent, patterns in self.intent_patterns.items():

            matched_patterns = []

            for pattern in patterns:

                if pattern in normalized_query:

                    matched_patterns.append(
                        pattern
                    )

            if matched_patterns:

                matches[intent] = matched_patterns

        # ----------------------------------------------------
        # No matching intent
        # ----------------------------------------------------

        if not matches:

            return {
                "intent": "UNKNOWN",
                "confidence": 0.0,
                "matched_patterns": []
            }

        # ----------------------------------------------------
        # Rank matched intents
        # More specific patterns are preferred.
        # ----------------------------------------------------

        ranked_matches = sorted(
            matches.items(),
            key=lambda item: (
                max(
                    len(pattern)
                    for pattern in item[1]
                ),
                len(item[1])
            ),
            reverse=True
        )

        best_intent = ranked_matches[0][0]

        best_matches = ranked_matches[0][1]

        best_pattern_length = max(
            len(pattern)
            for pattern in best_matches
        )

        # ----------------------------------------------------
        # Check whether another intent has an equally
        # specific matching pattern.
        # ----------------------------------------------------

        if len(ranked_matches) > 1:

            second_intent = ranked_matches[1][0]

            second_matches = ranked_matches[1][1]

            second_pattern_length = max(
                len(pattern)
                for pattern in second_matches
            )

            if (
                best_pattern_length
                == second_pattern_length
            ):

                return {
                    "intent": "AMBIGUOUS",
                    "confidence": 0.0,
                    "matched_patterns": (
                        best_matches
                        + second_matches
                    ),
                    "candidate_intents": [
                        best_intent,
                        second_intent
                    ]
                }

        # ----------------------------------------------------
        # Calculate confidence
        # ----------------------------------------------------

        if best_pattern_length >= 20:

            confidence = 1.0

        elif best_pattern_length >= 12:

            confidence = 0.85

        else:

            confidence = 0.70

        # ----------------------------------------------------
        # Return detected intent
        # ----------------------------------------------------

        return {
            "intent": best_intent,
            "confidence": confidence,
            "matched_patterns": best_matches
        }

    # ========================================================
    # CLASSIFIER
    # ========================================================

    def _get_classifier(self):

        if self._classifier is None:
            from backend.intent.intent_classifier import IntentClassifier
            self._classifier = IntentClassifier()

        return self._classifier

    def detect_classifier(self, query):

        return self._get_classifier().predict(query)

    # ========================================================
    # HYBRID DETECTION
    # ========================================================

    def detect(
        self,
        query
    ):

        rules = self.detect_rules(query)
        rules["method"] = "rules"

        if not self.use_classifier or not query or not query.strip():
            return rules

        try:
            model = self.detect_classifier(query)
        except Exception as e:
            print("Intent classifier unavailable, using rules:", str(e))
            return rules

        rule_intent = rules["intent"]
        model_intent = model["intent"]

        # A rule fired only on a short, generic keyword ("refund",
        # "payment", "certificate"): if the classifier confidently
        # picks a different specific intent, the classifier wins.
        # e.g. "cancel after the refund window" -> CANCELLATION.
        weak_rule = rules.get("confidence", 0.0) < 0.85

        if (
            rule_intent not in ("UNKNOWN", "AMBIGUOUS")
            and weak_rule
            and model_intent not in ("UNKNOWN", "AMBIGUOUS", rule_intent)
            and model["confidence"] >= 0.6
        ):
            return {
                "intent": model_intent,
                "confidence": model["confidence"],
                "matched_patterns": rules.get("matched_patterns", []),
                "method": "classifier (overrode weak rule)",
                "rules_intent": rule_intent
            }

        # Specific rule match: keep it; boost when the model agrees.
        if rule_intent not in ("UNKNOWN", "AMBIGUOUS"):

            if model_intent == rule_intent:
                rules["confidence"] = round(
                    max(rules["confidence"], model["confidence"], 0.9), 2
                )
                rules["method"] = "rules+classifier"

            rules["classifier"] = {
                "intent": model_intent,
                "confidence": model["confidence"]
            }

            return rules

        # Rules are ambiguous: the model breaks the tie if it picks
        # one of the candidates.
        if rule_intent == "AMBIGUOUS":

            if model_intent in rules.get("candidate_intents", []):
                return {
                    "intent": model_intent,
                    "confidence": model["confidence"],
                    "matched_patterns": rules.get("matched_patterns", []),
                    "method": "classifier (rule tie-break)"
                }

            return rules

        # No rule matched: trust the classifier (may be UNKNOWN).
        result = {
            "intent": model_intent,
            "confidence": model["confidence"],
            "matched_patterns": [],
            "method": "classifier"
        }

        if "candidate_intents" in model:
            result["candidate_intents"] = model["candidate_intents"]

        return result
