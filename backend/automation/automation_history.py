import json
import os
from datetime import datetime


class AutomationHistory:

    def __init__(
        self,
        history_directory="data/automation",
        history_file="execution_history.json",
        max_records=100
    ):

        self.history_directory = history_directory

        self.history_file = os.path.join(
            history_directory,
            history_file
        )

        self.max_records = max_records

        self._initialize_history()

    # ========================================================
    # INITIALIZE HISTORY
    # ========================================================

    def _initialize_history(self):

        os.makedirs(
            self.history_directory,
            exist_ok=True
        )

        if not os.path.exists(
            self.history_file
        ):

            with open(
                self.history_file,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    [],
                    file,
                    indent=4
                )

    # ========================================================
    # LOAD HISTORY
    # ========================================================

    def load(self):

        try:

            with open(
                self.history_file,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            if isinstance(
                data,
                list
            ):

                return data

            return []

        except Exception as e:

            print(
                "Unable to load automation history:",
                str(e)
            )

            return []

    # ========================================================
    # SAVE HISTORY
    # ========================================================

    def _save(
        self,
        records
    ):

        with open(
            self.history_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                records,
                file,
                indent=4
            )

    # ========================================================
    # RECORD EXECUTION
    # ========================================================

    def record(
        self,
        summary
    ):

        record = {

            "timestamp": (
                datetime.now().isoformat(
                    timespec="seconds"
                )
            ),

            "fetched": summary.get(
                "fetched",
                0
            ),

            "processed": summary.get(
                "processed",
                0
            ),

            "skipped": summary.get(
                "skipped",
                0
            ),

            "auto_reply": summary.get(
                "auto_reply",
                0
            ),

            "human_review": summary.get(
                "human_review",
                0
            ),

            "failed": summary.get(
                "failed",
                0
            )
        }

        records = self.load()

        records.append(
            record
        )

        # ----------------------------------------------------
        # Keep only the latest records.
        # ----------------------------------------------------

        records = records[
            -self.max_records:
        ]

        self._save(
            records
        )

        return record

    # ========================================================
    # CLEAR HISTORY
    # ========================================================

    def clear(self):

        self._save([])

    # ========================================================
    # LATEST RECORD
    # ========================================================

    def latest(self):

        records = self.load()

        if not records:

            return None

        return records[-1]
