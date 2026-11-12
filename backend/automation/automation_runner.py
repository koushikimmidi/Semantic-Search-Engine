import os
import json
import hashlib
import threading

from backend.automation.email_fetcher import EmailFetcher
from backend.automation.automation_service import AutomationService
from backend.automation.automation_history import AutomationHistory


class AutomationRunner:

    def __init__(
        self,
        send_emails=False,
        automation_service=None
    ):

        # ----------------------------------------------------
        # Configuration
        # ----------------------------------------------------

        self.send_emails = send_emails

        # ----------------------------------------------------
        # Email Fetcher
        # ----------------------------------------------------

        self.email_fetcher = EmailFetcher()

        # ----------------------------------------------------
        # Automation Service
        #
        # Reuse an existing service when provided.
        # This prevents creating a second SearchEngine and
        # RAG pipeline when the runner is used by FastAPI.
        # ----------------------------------------------------

        if automation_service is not None:

            self.automation_service = (
                automation_service
            )

        else:

            self.automation_service = (
                AutomationService(
                    send_emails=send_emails
                )
            )

        # ----------------------------------------------------
        # Processing State
        # ----------------------------------------------------

        self.state_directory = (
            "data/automation"
        )

        self.state_file = os.path.join(
            self.state_directory,
            "processed_messages.json"
        )

        # ----------------------------------------------------
        # Automation History
        # ----------------------------------------------------

        self.history = AutomationHistory(
            history_directory=self.state_directory
        )

        self.last_summary = {
            "fetched": 0,
            "processed": 0,
            "skipped": 0,
            "auto_reply": 0,
            "human_review": 0,
            "failed": 0
        }

        # Prevents the scheduler and a manual /automation/run from
        # processing the same inbox at the same time.
        self._run_lock = threading.Lock()

        self._initialize_state()

    # ========================================================
    # INITIALIZE STATE
    # ========================================================

    def _initialize_state(self):

        os.makedirs(
            self.state_directory,
            exist_ok=True
        )

        if not os.path.exists(
            self.state_file
        ):

            with open(
                self.state_file,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    [],
                    file,
                    indent=4
                )

    # ========================================================
    # LOAD PROCESSED MESSAGE IDS
    # ========================================================

    def _load_processed_messages(self):

        try:

            with open(
                self.state_file,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            if isinstance(
                data,
                list
            ):

                return set(data)

            return set()

        except Exception as e:

            print(
                "Unable to load processing state:",
                str(e)
            )

            return set()

    # ========================================================
    # SAVE PROCESSED MESSAGE IDS
    # ========================================================

    def _save_processed_messages(
        self,
        processed_messages
    ):

        with open(
            self.state_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                sorted(
                    processed_messages
                ),
                file,
                indent=4
            )

    # ========================================================
    # GENERATE MESSAGE ID
    # ========================================================

    def _generate_message_id(
        self,
        message
    ):

        sender = message.get(
            "sender",
            ""
        )

        subject = message.get(
            "subject",
            ""
        )

        body = message.get(
            "body",
            ""
        )

        raw_identifier = (
            sender
            + "|"
            + subject
            + "|"
            + body
        )

        message_id = hashlib.sha256(
            raw_identifier.encode(
                "utf-8"
            )
        ).hexdigest()

        return message_id

    # ========================================================
    # ADD TEST MESSAGES
    # ========================================================

    def add_test_messages(self):

        # ----------------------------------------------------
        # Test Message 1
        # Expected: AUTO_REPLY
        # ----------------------------------------------------

        self.email_fetcher.add_message(
            "student1@example.com",
            "Refund request",
            "What is the refund period for my course?"
        )

        # ----------------------------------------------------
        # Test Message 2
        # Expected: HUMAN_REVIEW
        # ----------------------------------------------------

        self.email_fetcher.add_message(
            "student2@example.com",
            "General question",
            "What is the capital of Japan?"
        )

    # ========================================================
    # RUN AUTOMATION
    # ========================================================

    def run(self):

        if not self._run_lock.acquire(blocking=False):
            raise RuntimeError(
                "An automation run is already in progress."
            )

        try:
            return self._run()
        finally:
            self._run_lock.release()

    def _run(self):

        print("")
        print("=" * 60)
        print("AUTOMATION RUNNER")
        print("=" * 60)

        # ----------------------------------------------------
        # Load processing state
        # ----------------------------------------------------

        processed_messages = (
            self._load_processed_messages()
        )

        # ----------------------------------------------------
        # Fetch Messages
        # ----------------------------------------------------

        messages = (
            self.email_fetcher.fetch_messages()
        )

        print(
            f"Messages fetched: {len(messages)}"
        )

        # ----------------------------------------------------
        # Counters
        # ----------------------------------------------------

        skipped_count = 0

        # ----------------------------------------------------
        # Results
        # ----------------------------------------------------

        results = []

        # ----------------------------------------------------
        # Process Messages
        # ----------------------------------------------------

        for index, message in enumerate(
            messages,
            start=1
        ):

            message_id = (
                self._generate_message_id(
                    message
                )
            )

            # ------------------------------------------------
            # Skip already processed messages
            # ------------------------------------------------

            if message_id in processed_messages:

                skipped_count += 1

                print("")
                print(
                    f"Skipping message {index}"
                )

                print(
                    "Reason: Message was already "
                    "processed successfully."
                )

                continue

            # ------------------------------------------------
            # Process new message
            # ------------------------------------------------

            print("")
            print(
                f"Processing message {index}"
            )

            print(
                f"Sender: {message.get('sender', '')}"
            )

            print(
                f"Subject: {message.get('subject', '')}"
            )

            result = (
                self.automation_service
                .process_message(message)
            )

            results.append(
                result
            )

            print(
                f"Route: {result.get('route')}"
            )

            # ------------------------------------------------
            # Mark as processed ONLY when successful
            # ------------------------------------------------

            if result.get(
                "success",
                False
            ):

                processed_messages.add(
                    message_id
                )

                self._save_processed_messages(
                    processed_messages
                )

        # ----------------------------------------------------
        # Summary
        # ----------------------------------------------------

        auto_reply_count = sum(
            1
            for result in results
            if result.get("route")
            == "AUTO_REPLY"
        )

        human_review_count = sum(
            1
            for result in results
            if result.get("route")
            == "HUMAN_REVIEW"
        )

        failed_count = sum(
            1
            for result in results
            if not result.get(
                "success",
                False
            )
        )

        self.last_summary = {
            "fetched": len(messages),
            "processed": len(results),
            "skipped": skipped_count,
            "auto_reply": auto_reply_count,
            "human_review": human_review_count,
            "failed": failed_count
        }

        # ----------------------------------------------------
        # Persist execution history
        # ----------------------------------------------------

        history_record = self.history.record(
            self.last_summary
        )

        print(
            "History recorded:",
            history_record["timestamp"]
        )

        print("")
        print("=" * 60)
        print("AUTOMATION SUMMARY")
        print("=" * 60)

        print(
            f"FETCHED: {len(messages)}"
        )

        print(
            f"PROCESSED: {len(results)}"
        )

        print(
            f"SKIPPED: {skipped_count}"
        )

        print(
            f"AUTO_REPLY: {auto_reply_count}"
        )

        print(
            f"HUMAN_REVIEW: {human_review_count}"
        )

        print(
            f"FAILED: {failed_count}"
        )

        print("=" * 60)

        return results


# ============================================================
# REAL GMAIL AUTOMATION
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Safe mode
    #
    # Real emails will NOT be sent.
    # --------------------------------------------------------

    runner = AutomationRunner(
        send_emails=False
    )

    # --------------------------------------------------------
    # Run real Gmail automation
    # --------------------------------------------------------

    results = runner.run()

    print("")
    print("RESULTS:")
    print(results)
