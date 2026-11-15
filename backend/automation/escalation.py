import json
import os
import threading
import uuid
from datetime import datetime


class EscalationManager:
    """
    Human review queue.

    Messages the Confidence Engine does not approve for automatic
    reply are stored here so a support agent can review them.
    The queue is persisted to disk so it survives API restarts.
    """

    PENDING = "PENDING"
    RESOLVED = "RESOLVED"

    def __init__(
        self,
        storage_directory="data/automation",
        storage_file="escalations.json",
        max_records=500
    ):

        self.storage_directory = storage_directory

        self.storage_file = os.path.join(
            storage_directory,
            storage_file
        )

        self.max_records = max_records

        self._lock = threading.Lock()

        os.makedirs(
            self.storage_directory,
            exist_ok=True
        )

        self.escalated_messages = self._load()

    # ========================================================
    # PERSISTENCE
    # ========================================================

    def _load(self):

        if not os.path.exists(self.storage_file):
            return []

        try:

            with open(
                self.storage_file,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            return data if isinstance(data, list) else []

        except Exception as e:

            print(
                "Unable to load escalations:",
                str(e)
            )

            return []

    def _save(self):

        temp_file = self.storage_file + ".tmp"

        with open(
            temp_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.escalated_messages,
                file,
                indent=4,
                ensure_ascii=False
            )

        os.replace(temp_file, self.storage_file)

    # ========================================================
    # ESCALATE MESSAGE
    # ========================================================

    def escalate(
        self,
        message,
        confidence_result,
        reason=None,
        suggested_answer=None,
        intent=None
    ):

        escalation = {

            "id": uuid.uuid4().hex,

            "timestamp": datetime.now().isoformat(
                timespec="seconds"
            ),

            "status": self.PENDING,

            "sender": message.get(
                "sender",
                ""
            ),

            # Needed to send a threaded reply later.
            "sender_email": message.get("sender_email", ""),
            "message_id": message.get("message_id", ""),
            "references": message.get("references", []),

            "subject": message.get(
                "subject",
                ""
            ),

            "body": message.get(
                "body",
                ""
            ),

            "suggested_answer": suggested_answer,

            "intent": intent,

            "confidence": confidence_result,

            "reason": (
                reason
                or
                "Message requires human review."
            ),

            "resolved_at": None,

            "resolution_note": None,

            "reply": None
        }

        with self._lock:

            self.escalated_messages.append(
                escalation
            )

            # Keep the file bounded; drop the oldest resolved first.
            if len(self.escalated_messages) > self.max_records:

                pending = [
                    item for item in self.escalated_messages
                    if item.get("status") == self.PENDING
                ]

                resolved = [
                    item for item in self.escalated_messages
                    if item.get("status") != self.PENDING
                ]

                overflow = (
                    len(self.escalated_messages)
                    - self.max_records
                )

                resolved = resolved[overflow:]

                self.escalated_messages = sorted(
                    pending + resolved,
                    key=lambda item: item.get("timestamp", "")
                )

            self._save()

        return escalation

    # ========================================================
    # GET ESCALATED MESSAGES
    # ========================================================

    def get_escalated_messages(self, status=None):

        with self._lock:

            records = list(self.escalated_messages)

        if status:

            records = [
                item for item in records
                if item.get("status") == status.upper()
            ]

        # Newest first.
        return list(reversed(records))

    # ========================================================
    # RESOLVE ESCALATION
    # ========================================================

    def get(self, escalation_id):

        with self._lock:

            for item in self.escalated_messages:

                if item.get("id") == escalation_id:
                    return dict(item)

        return None

    def resolve(self, escalation_id, resolution_note=None, reply=None, resolved_by=None):

        with self._lock:

            for item in self.escalated_messages:

                if item.get("id") == escalation_id:

                    item["status"] = self.RESOLVED

                    item["resolved_at"] = datetime.now().isoformat(
                        timespec="seconds"
                    )

                    item["resolution_note"] = resolution_note

                    if reply is not None:
                        item["reply"] = reply

                    if resolved_by:
                        item["resolved_by"] = resolved_by

                    self._save()

                    return item

        return None

    # ========================================================
    # CLEAR ESCALATIONS
    # ========================================================

    def clear(self):

        with self._lock:

            self.escalated_messages = []

            self._save()
