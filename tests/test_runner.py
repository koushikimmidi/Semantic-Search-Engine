import pytest

from backend.automation.automation_runner import AutomationRunner
from backend.automation.escalation import EscalationManager


class StubService:

    def __init__(self, fail_on=None):
        self.fail_on = fail_on
        self.seen = []

    def process_message(self, message):

        self.seen.append(message["subject"])

        if message.get("automated"):
            return {"success": True, "route": "SKIPPED"}

        if message["subject"] == self.fail_on:
            raise RuntimeError("boom")

        return {"success": True, "route": "HUMAN_REVIEW"}


def _runner(tmp_path, service):

    runner = AutomationRunner(automation_service=service, state_directory=str(tmp_path))
    runner.email_fetcher.messages = []

    return runner


def _message(subject, uid=None, automated=False):

    return {
        "uid": uid,
        "message_id": f"<{subject}@example.com>",
        "references": [],
        "sender": "s@example.com",
        "sender_email": "s@example.com",
        "subject": subject,
        "body": "question",
        "automated": automated
    }


def test_runner_dedupes_by_message_id_and_skips_automated(tmp_path):

    service = StubService()
    runner = _runner(tmp_path, service)

    runner.email_fetcher.messages = [
        _message("a"),
        _message("newsletter", automated=True),
    ]

    runner.run()

    assert runner.last_summary["processed"] == 1
    assert runner.last_summary["skipped"] == 1

    runner.run()   # same messages again

    assert runner.last_summary["processed"] == 0
    assert runner.last_summary["skipped"] == 2


def test_one_failing_message_does_not_stop_the_run(tmp_path):

    service = StubService(fail_on="bad")
    runner = _runner(tmp_path, service)

    runner.email_fetcher.messages = [_message("bad"), _message("good")]

    runner.run()

    assert service.seen == ["bad", "good"]
    assert runner.last_summary["failed"] == 1
    assert runner.last_summary["processed"] == 2

    # The failed message is retried next time, the good one is not.
    service.seen.clear()
    runner.run()

    assert service.seen == ["bad"]


def test_mark_as_read_only_when_enabled(tmp_path):

    runner = _runner(tmp_path, StubService())

    marked = []
    runner.email_fetcher.mark_as_read = lambda uids: marked.extend(uids) or len(uids)
    runner.email_fetcher.messages = [_message("a", uid="7")]

    runner.email_fetcher.mark_processed_as_read = False
    runner.run()
    assert marked == []

    runner.email_fetcher.messages = [_message("b", uid="8")]
    runner.email_fetcher.mark_processed_as_read = True
    runner.run()
    assert marked == ["8"]


def test_concurrent_run_is_rejected(tmp_path):

    runner = _runner(tmp_path, StubService())

    runner._run_lock.acquire()

    try:
        with pytest.raises(RuntimeError):
            runner.run()
    finally:
        runner._run_lock.release()


def test_escalation_queue_persists_and_resolves(tmp_path):

    manager = EscalationManager(storage_directory=str(tmp_path))

    item = manager.escalate({"sender": "a", "subject": "s", "body": "b"}, {"level": "LOW"})

    reloaded = EscalationManager(storage_directory=str(tmp_path))

    assert reloaded.get(item["id"])["status"] == "PENDING"
    assert reloaded.resolve(item["id"], "done", reply="hi")["reply"] == "hi"
    assert reloaded.get_escalated_messages("PENDING") == []
    assert reloaded.resolve("missing") is None
