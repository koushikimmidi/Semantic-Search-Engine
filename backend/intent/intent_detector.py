import re


class IntentDetector:

    def __init__(self):

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

    def detect(
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