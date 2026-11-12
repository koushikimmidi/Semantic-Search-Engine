import threading
import time
from datetime import datetime

from backend.automation.automation_runner import AutomationRunner


class AutomationScheduler:

    def __init__(
        self,
        interval_seconds=300,
        send_emails=False,
        automation_runner=None
    ):

        # ----------------------------------------------------
        # Configuration
        # ----------------------------------------------------

        self.interval_seconds = interval_seconds
        self.send_emails = send_emails

        # ----------------------------------------------------
        # Automation Runner
        #
        # Reuse an existing runner when supplied. This is
        # important for the FastAPI application because the
        # runner already uses the API's loaded SearchEngine
        # and RAGPipeline.
        # ----------------------------------------------------

        if automation_runner is not None:

            self.runner = automation_runner

        else:

            self.runner = AutomationRunner(
                send_emails=send_emails
            )

        # ----------------------------------------------------
        # Scheduler state
        # ----------------------------------------------------

        self.running = False
        self.thread = None

    # ========================================================
    # RUN ONE CYCLE
    # ========================================================

    def run_once(self):

        print("")
        print("=" * 60)
        print("AUTOMATION SCHEDULER")
        print("=" * 60)

        print(
            "Cycle started:",
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        try:

            results = self.runner.run()

            print("")
            print(
                "Cycle completed successfully."
            )

            return results

        except Exception as e:

            print("")
            print(
                "Scheduler cycle failed:",
                str(e)
            )

            return []

    # ========================================================
    # BACKGROUND LOOP
    # ========================================================

    def _run_loop(self):

        while self.running:

            self.run_once()

            if not self.running:

                break

            print("")
            print(
                f"Next check in "
                f"{self.interval_seconds} seconds..."
            )

            # Use small waits so stop requests do not need
            # to wait for the complete interval.
            remaining = self.interval_seconds

            while (
                self.running
                and remaining > 0
            ):

                time.sleep(
                    min(1, remaining)
                )

                remaining -= 1

    # ========================================================
    # START SCHEDULER
    # ========================================================

    def start(self):

        if self.running:

            return False

        self.running = True

        self.thread = threading.Thread(
            target=self._run_loop,
            name="AutomationScheduler",
            daemon=True
        )

        self.thread.start()

        print("")
        print("=" * 60)
        print("AUTOMATION SCHEDULER STARTED")
        print("=" * 60)

        print(
            f"Check interval: "
            f"{self.interval_seconds} seconds"
        )

        print(
            "Email sending:",
            self.send_emails
        )

        print("=" * 60)

        return True

    # ========================================================
    # STOP SCHEDULER
    # ========================================================

    def stop(self):

        if not self.running:

            return False

        self.running = False

        current_thread = (
            threading.current_thread()
        )

        if (
            self.thread is not None
            and self.thread is not current_thread
            and self.thread.is_alive()
        ):

            self.thread.join(
                timeout=2
            )

        self.thread = None

        print("")
        print(
            "Automation scheduler stopped."
        )

        return True

    # ========================================================
    # STATUS
    # ========================================================

    def status(self):

        return {
            "running": self.running,
            "interval_seconds": (
                self.interval_seconds
            ),
            "email_sending": (
                self.send_emails
            )
        }


# ============================================================
# COMMAND-LINE ENTRY POINT
# ============================================================

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Gmail automation scheduler"
        )
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help=(
            "Interval between Gmail checks "
            "in seconds. Default: 300."
        )
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help=(
            "Run one automation cycle "
            "and exit."
        )
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # Safe mode
    #
    # Real emails will NOT be sent.
    # --------------------------------------------------------

    scheduler = AutomationScheduler(
        interval_seconds=args.interval,
        send_emails=False
    )

    # --------------------------------------------------------
    # One-cycle test
    # --------------------------------------------------------

    if args.once:

        scheduler.run_once()

    # --------------------------------------------------------
    # Continuous scheduler
    # --------------------------------------------------------

    else:

        scheduler.start()

        try:

            while scheduler.running:

                time.sleep(1)

        except KeyboardInterrupt:

            scheduler.stop()
