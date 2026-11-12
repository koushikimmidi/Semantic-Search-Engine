class MessageRouter:

    def __init__(self):

        # ----------------------------------------------------
        # Allowed routing decisions
        # ----------------------------------------------------

        self.AUTO_REPLY = "AUTO_REPLY"

        self.HUMAN_REVIEW = "HUMAN_REVIEW"

    # ========================================================
    # ROUTE MESSAGE
    # ========================================================

    def route(
        self,
        confidence_result
    ):

        # ----------------------------------------------------
        # Validate input
        # ----------------------------------------------------

        if not confidence_result:

            return {

                "route": self.HUMAN_REVIEW,

                "reason": (
                    "No confidence result was provided."
                )

            }

        # ----------------------------------------------------
        # Read decision
        # ----------------------------------------------------

        decision = confidence_result.get(
            "decision",
            self.HUMAN_REVIEW
        )

        # ----------------------------------------------------
        # AUTO_REPLY
        #
        # Only allow automatic reply when the Confidence
        # Engine explicitly approves it.
        # ----------------------------------------------------

        if decision == self.AUTO_REPLY:

            return {

                "route": self.AUTO_REPLY,

                "reason": (
                    "Confidence Engine approved "
                    "automatic reply."
                )

            }

        # ----------------------------------------------------
        # Everything else goes to human review.
        #
        # This includes:
        #
        # MEDIUM
        # LOW
        # UNKNOWN
        # Invalid decisions
        # ----------------------------------------------------

        return {

            "route": self.HUMAN_REVIEW,

            "reason": (
                "Confidence Engine did not approve "
                "automatic reply."
            )

        }