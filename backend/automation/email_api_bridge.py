import requests

from backend.automation.email_fetcher import EmailFetcher


class EmailAPIBridge:

    def __init__(
        self,
        api_url="http://localhost:8000/automation/process"
    ):

        # ----------------------------------------------------
        # Automation API
        # ----------------------------------------------------

        self.api_url = api_url

        # ----------------------------------------------------
        # Email Fetcher
        # ----------------------------------------------------

        self.email_fetcher = EmailFetcher()

    # ========================================================
    # SEND MESSAGE TO AUTOMATION API
    # ========================================================

    def process_message(
        self,
        message
    ):

        try:

            response = requests.post(
                self.api_url,
                json=message,
                timeout=120
            )

            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:

            return {

                "success": False,

                "error": (
                    "Failed to connect to "
                    "Automation API: "
                    f"{str(e)}"
                )

            }

    # ========================================================
    # PROCESS ALL FETCHED EMAILS
    # ========================================================

    def process_messages(self):

        messages = (
            self.email_fetcher.fetch_messages()
        )

        results = []

        for message in messages:

            result = self.process_message(
                message
            )

            results.append(
                result
            )

        return results


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    bridge = EmailAPIBridge()

    # --------------------------------------------------------
    # Add test email
    # --------------------------------------------------------

    bridge.email_fetcher.add_message(
        "student@example.com",
        "Refund request",
        "What is the refund period for my course?"
    )

    # --------------------------------------------------------
    # Add unknown email
    # --------------------------------------------------------

    bridge.email_fetcher.add_message(
        "student2@example.com",
        "General question",
        "What is the capital of Japan?"
    )

    # --------------------------------------------------------
    # Process emails
    # --------------------------------------------------------

    results = bridge.process_messages()

    # --------------------------------------------------------
    # Display results
    # --------------------------------------------------------

    print(
        "\n"
        + "=" * 60
    )

    print(
        "EMAIL API BRIDGE RESULTS"
    )

    print(
        "=" * 60
    )

    for index, result in enumerate(
        results,
        start=1
    ):

        print(
            f"\nEMAIL {index}"
        )

        print(
            "-" * 40
        )

        print(
            "Success:",
            result.get("success")
        )

        print(
            "Route:",
            result.get("route")
        )

        print(
            "Answer:",
            result.get("answer")
        )

        print(
            "Intent:",
            result.get("intent")
        )

        print(
            "Confidence:",
            result.get("confidence")
        )

    print(
        "\n"
        + "=" * 60
    )