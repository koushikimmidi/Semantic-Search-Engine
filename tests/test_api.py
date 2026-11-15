import json
import os

from tests.conftest import ADMIN, AGENT


# ============================================================
# AUTH
# ============================================================

def test_auth_me_reports_roles(api):

    assert api.get("/auth/me").json()["role"] == "viewer"
    assert api.get("/auth/me", headers=AGENT).json()["role"] == "agent"
    assert api.get("/auth/me", headers=ADMIN).json()["role"] == "admin"
    assert api.get("/auth/me", headers={"X-API-Key": "wrong"}).json()["role"] == "viewer"


def test_role_requirements(api):

    # Viewer: search + browse only.
    assert api.post("/search", json={"query": "refund"}).status_code == 200
    assert api.get("/documents").status_code == 200
    assert api.get("/automation/dashboard").status_code == 401

    # Agent: automation but not document management or scheduler.
    assert api.get("/automation/dashboard", headers=AGENT).status_code == 200
    assert api.delete("/documents", params={"path": "password_reset.md"}, headers=AGENT).status_code == 403
    assert api.post("/automation/scheduler/start", headers=AGENT).status_code == 403

    # Admin: everything.
    assert api.post("/automation/scheduler/stop", headers=ADMIN).status_code == 200


def test_auth_disabled_without_keys(api, monkeypatch):

    monkeypatch.delenv("ADMIN_API_KEY")
    monkeypatch.delenv("AGENT_API_KEY")

    info = api.get("/auth/me").json()

    assert info["role"] == "admin"
    assert info["auth_enabled"] is False
    assert info["method"] == "disabled"


# ============================================================
# SEARCH
# ============================================================

def test_search_returns_answer_with_citations(api):

    response = api.post("/search", json={"query": "refund within 7 calendar days"}).json()

    assert response["success"] is True
    assert response["sources"][0]["source"] == "policies/refund_policy.txt"
    assert "[1]" in response["answer"]
    assert response["intent"]["intent"] == "REFUND"


def test_search_stream_ndjson(api):

    with api.stream("POST", "/search/stream", json={"query": "password reset email"}) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/x-ndjson")
        events = [json.loads(line) for line in response.iter_lines() if line]

    assert events[0]["type"] == "sources"
    assert events[-1]["type"] == "done" and events[-1]["success"] is True
    assert "".join(e["text"] for e in events if e["type"] == "token") == events[-1]["answer"]


def test_empty_query(api):

    response = api.post("/search", json={"query": "   "}).json()

    assert response["routing"]["route"] == "HUMAN_REVIEW"


# ============================================================
# DOCUMENTS
# ============================================================

def test_path_traversal_is_blocked(api, tmp_path):

    outside = tmp_path / "secret.txt"
    outside.write_text("secret", encoding="utf-8")

    for bad in [str(outside), "../secret.txt", "/etc/passwd", "..\\secret.txt"]:
        assert api.get("/documents/content", params={"path": bad}).json()["success"] is False
        assert api.delete("/documents", params={"path": bad}, headers=ADMIN).json()["success"] is False

    assert outside.exists()


def test_upload_search_delete_roundtrip(api):

    engine = api.app_module.engine
    loads_before = engine.loads

    upload = api.post(
        "/documents/upload",
        headers=ADMIN,
        files=[
            ("files", ("library.txt", b"The campus library opens at nine.", "text/plain")),
            ("files", ("virus.exe", b"MZ", "application/octet-stream"))
        ],
        data={"paths": ["new/library.txt", "virus.exe"]}
    ).json()

    assert upload == {"success": True, "count": 1, "skipped": ["virus.exe"]}
    assert engine.loads == loads_before + 1

    paths = [d["path"] for d in api.get("/documents").json()]
    assert "new/library.txt" in paths

    content = api.get("/documents/content", params={"path": "new/library.txt"}).json()
    assert "library opens" in content["content"]

    assert api.delete("/documents", params={"path": "new/library.txt"}, headers=ADMIN).json()["success"]

    kb = os.environ["KNOWLEDGE_BASE_PATH"]
    assert not os.path.exists(os.path.join(kb, "new"))   # empty folder removed


# ============================================================
# AUTOMATION
# ============================================================

def test_process_routes_and_queues_for_review(api):

    off_topic = api.post(
        "/automation/process",
        headers=AGENT,
        json={"sender": "s@example.com", "subject": "Hi", "body": "What is the capital of Japan?"}
    ).json()

    assert off_topic["route"] == "HUMAN_REVIEW"

    queue = api.get("/automation/escalations", params={"status": "PENDING"}, headers=AGENT).json()

    assert queue["count"] == 1
    assert queue["escalations"][0]["id"] == off_topic["escalation"]["id"]
    assert api.get("/automation/dashboard", headers=AGENT).json()["dashboard"]["pending_reviews"] == 1


def test_reply_requires_smtp_and_keeps_item_pending(api):

    item = api.post(
        "/automation/process",
        headers=AGENT,
        json={"sender": "s@example.com", "subject": "Hi", "body": "Tell me a joke"}
    ).json()["escalation"]

    result = api.post(
        f"/automation/escalations/{item['id']}/reply",
        headers=AGENT,
        json={"reply": "Hello!"}
    ).json()

    assert result["success"] is False
    assert "SMTP" in result["error"]
    assert api.get("/automation/escalations", params={"status": "PENDING"}, headers=AGENT).json()["count"] == 1


def test_reply_sends_threaded_email_and_resolves(api, monkeypatch):

    service = api.app_module.automation_service
    sent = {}

    def fake_send(**kwargs):
        sent.update(kwargs)
        return {"success": True, "sent": True}

    monkeypatch.setattr(service.email_sender, "is_configured", lambda: True)
    monkeypatch.setattr(service.email_sender, "send_email", fake_send)

    item = service.escalation_manager.escalate(
        {
            "sender": "Student <s@example.com>",
            "sender_email": "s@example.com",
            "subject": "Certificate",
            "body": "Where is my certificate?",
            "message_id": "<m1@example.com>",
            "references": ["<m1@example.com>"]
        },
        {"decision": "HUMAN_REVIEW"}
    )

    result = api.post(
        f"/automation/escalations/{item['id']}/reply",
        headers=AGENT,
        json={"reply": "It is in your portal."}
    ).json()

    assert result["success"] is True
    assert result["escalation"]["status"] == "RESOLVED"
    assert result["escalation"]["reply"] == "It is in your portal."
    assert sent["recipient"] == "s@example.com"
    assert sent["subject"] == "Re: Certificate"
    assert sent["in_reply_to"] == "<m1@example.com>"

    again = api.post(f"/automation/escalations/{item['id']}/reply", headers=AGENT, json={"reply": "x"}).json()
    assert again["success"] is False


def test_automation_run_without_email_account(api):

    # Inbox checks are an admin control.
    assert api.post("/automation/run", headers=AGENT).status_code == 403

    response = api.post("/automation/run", headers=ADMIN).json()

    assert response["success"] is True
    assert response["summary"]["fetched"] == 0


def test_fallback_answer_is_not_offered_as_draft(api):

    service = api.app_module.automation_service

    item = service._escalate(
        {"sender": "a", "subject": "s", "body": "b"},
        {"decision": "HUMAN_REVIEW"},
        "reason",
        "I cannot answer this based on the provided documents.",
        {"intent": "UNKNOWN"}
    )

    assert item["suggested_answer"] is None

    drafted = service._escalate(
        {"sender": "a", "subject": "s", "body": "b"},
        {"decision": "HUMAN_REVIEW"},
        "reason",
        "Refunds take 7 days [1].",
        {"intent": "REFUND"}
    )

    assert drafted["suggested_answer"] == "Refunds take 7 days."
