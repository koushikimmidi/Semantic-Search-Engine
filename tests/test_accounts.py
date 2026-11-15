import time

import pytest

from backend.accounts import AccountError, TokenSigner, UserStore, hash_password, verify_password
from backend.storage import AppDatabase

from tests.conftest import ADMIN


# ============================================================
# SECURITY PRIMITIVES
# ============================================================

def test_password_hash_roundtrip():

    stored = hash_password("correct horse")

    assert stored.startswith("pbkdf2_sha256$")
    assert verify_password("correct horse", stored)
    assert not verify_password("wrong", stored)
    assert not verify_password("x", "garbage")


def test_token_sign_verify_tamper_and_expiry(tmp_path):

    signer = TokenSigner(secret="s3cret", ttl_seconds=60)
    token = signer.create(1, "alice", "admin")

    assert signer.verify(token)["sub"] == "alice"
    assert signer.verify(token + "x") is None
    assert TokenSigner(secret="other").verify(token) is None

    expired = TokenSigner(secret="s3cret", ttl_seconds=-1).create(1, "alice", "admin")
    assert signer.verify(expired) is None

    # Without AUTH_SECRET a secret file is created once and reused.
    secret_file = tmp_path / "secret.key"
    first = TokenSigner(secret_file=str(secret_file)).create(2, "bob", "employee")
    assert TokenSigner(secret_file=str(secret_file)).verify(first)["uid"] == 2


# ============================================================
# USER STORE
# ============================================================

@pytest.fixture
def store(tmp_path):

    return UserStore(AppDatabase(str(tmp_path / "app.db")))


def test_create_validate_and_authenticate(store):

    store.create("admin1", "password123", "admin", "Admin One")

    with pytest.raises(AccountError):
        store.create("admin1", "password123")          # duplicate
    with pytest.raises(AccountError):
        store.create("x", "password123")               # bad username
    with pytest.raises(AccountError):
        store.create("bob", "short")                   # weak password
    with pytest.raises(AccountError):
        store.create("bob", "password123", "boss")     # bad role

    assert store.authenticate("ADMIN1", "password123")["username"] == "admin1"

    with pytest.raises(AccountError):
        store.authenticate("admin1", "nope")


def test_last_admin_is_protected(store):

    admin = store.create("admin1", "password123", "admin")

    with pytest.raises(AccountError):
        store.update(admin["id"], role="employee")
    with pytest.raises(AccountError):
        store.update(admin["id"], active=False)
    with pytest.raises(AccountError):
        store.delete(admin["id"])

    store.create("admin2", "password123", "admin")

    assert store.update(admin["id"], role="employee")["role"] == "employee"


def test_disabled_user_cannot_log_in(store):

    store.create("admin1", "password123", "admin")
    emp = store.create("emp", "password123", "employee")

    store.update(emp["id"], active=False)

    with pytest.raises(AccountError):
        store.authenticate("emp", "password123")


def test_lockout_after_repeated_failures(store, monkeypatch):

    store.create("emp", "password123", "employee")

    for _ in range(5):
        with pytest.raises(AccountError):
            store.authenticate("emp", "wrong-password")

    with pytest.raises(AccountError, match="Too many"):
        store.authenticate("emp", "password123")

    # After the lockout window the right password works again.
    real_time = time.time
    monkeypatch.setattr(time, "time", lambda: real_time() + 301)

    assert store.authenticate("emp", "password123")["username"] == "emp"


# ============================================================
# API: SETUP, LOGIN, ROLES
# ============================================================

def _setup_admin(api):

    response = api.post("/auth/setup", json={
        "setup_key": "admin-test-key",
        "username": "boss",
        "password": "boss-password",
        "full_name": "The Boss"
    })

    assert response.status_code == 200, response.text

    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_setup_requires_admin_key_and_runs_once(api):

    assert api.get("/auth/status").json()["setup_required"] is True

    bad = api.post("/auth/setup", json={"setup_key": "nope", "username": "boss", "password": "boss-password"})
    assert bad.status_code == 403

    headers = _setup_admin(api)

    me = api.get("/auth/me", headers=headers).json()
    assert me["role"] == "admin" and me["username"] == "boss" and me["method"] == "account"

    again = api.post("/auth/setup", json={"setup_key": "admin-test-key", "username": "x2", "password": "password123"})
    assert again.status_code == 409
    assert api.get("/auth/status").json()["setup_required"] is False


def test_admin_creates_employee_with_limited_access(api):

    admin = _setup_admin(api)

    created = api.post("/admin/users", headers=admin, json={
        "username": "emma", "password": "emma-password", "role": "employee", "full_name": "Emma"
    })
    assert created.status_code == 200, created.text

    login = api.post("/auth/login", json={"username": "emma", "password": "emma-password"})
    assert login.status_code == 200
    emp = {"Authorization": f"Bearer {login.json()['token']}"}

    # Employees: queue, analytics, test messages.
    assert api.get("/automation/escalations", headers=emp).status_code == 200
    assert api.get("/analytics/overview", headers=emp).status_code == 200

    # Not: users, settings, audit, documents, scheduler, inbox runs.
    for method, path in [
        ("get", "/admin/users"), ("get", "/admin/audit"), ("get", "/admin/system"),
        ("post", "/automation/run"), ("post", "/automation/scheduler/start"),
        ("post", "/admin/reindex")
    ]:
        assert getattr(api, method)(path, headers=emp).status_code == 403, path

    assert api.delete("/documents", params={"path": "password_reset.md"}, headers=emp).status_code == 403


def test_wrong_password_and_bad_token(api):

    _setup_admin(api)

    assert api.post("/auth/login", json={"username": "boss", "password": "bad"}).status_code == 401

    bogus = {"Authorization": "Bearer not.a-token"}
    assert api.get("/auth/me", headers=bogus).json()["role"] == "viewer"
    assert api.get("/automation/escalations", headers=bogus).status_code == 401


def test_disabling_user_revokes_access_immediately(api):

    admin = _setup_admin(api)

    user = api.post("/admin/users", headers=admin, json={"username": "emma", "password": "emma-password"}).json()["user"]
    token = api.post("/auth/login", json={"username": "emma", "password": "emma-password"}).json()["token"]
    emp = {"Authorization": f"Bearer {token}"}

    assert api.get("/automation/escalations", headers=emp).status_code == 200

    api.patch(f"/admin/users/{user['id']}", headers=admin, json={"active": False})

    assert api.get("/automation/escalations", headers=emp).status_code == 401


def test_change_password(api):

    admin = _setup_admin(api)

    bad = api.post("/auth/change-password", headers=admin, json={"current_password": "x", "new_password": "new-password"})
    assert bad.status_code == 400

    ok = api.post("/auth/change-password", headers=admin, json={"current_password": "boss-password", "new_password": "new-password"})
    assert ok.status_code == 200

    assert api.post("/auth/login", json={"username": "boss", "password": "new-password"}).status_code == 200


def test_admin_cannot_delete_self_or_last_admin(api):

    admin = _setup_admin(api)
    me = api.get("/admin/users", headers=admin).json()["users"][0]

    assert api.delete(f"/admin/users/{me['id']}", headers=admin).status_code == 400
    assert api.patch(f"/admin/users/{me['id']}", headers=admin, json={"role": "employee"}).status_code == 400


def test_api_key_still_works_alongside_accounts(api):

    _setup_admin(api)

    assert api.get("/admin/users", headers=ADMIN).status_code == 200


# ============================================================
# AUDIT, ANALYTICS, SETTINGS
# ============================================================

def test_actions_are_audited(api):

    admin = _setup_admin(api)

    api.post("/admin/users", headers=admin, json={"username": "emma", "password": "emma-password"})
    api.post("/auth/login", json={"username": "emma", "password": "wrong-pass"})

    audit = api.get("/admin/audit", headers=admin).json()
    actions = [item["action"] for item in audit["items"]]

    assert "setup_admin_created" in actions
    assert "user_created" in actions
    assert "login_failed" in actions
    assert audit["items"][0]["timestamp"] >= audit["items"][-1]["timestamp"]


def test_analytics_overview_counts_activity(api):

    admin = _setup_admin(api)

    api.post("/search", headers=admin, json={"query": "refund within 7 calendar days"})
    api.post("/automation/process", headers=admin, json={
        "sender": "s@example.com", "subject": "Joke", "body": "Tell me a joke"
    })

    overview = api.get("/analytics/overview", params={"days": 7}, headers=admin).json()["overview"]

    assert overview["searches"]["total"] == 1
    assert overview["emails"]["total"] == 1
    assert overview["emails"]["human_review"] == 1
    assert overview["emails"]["by_channel"] == {"test": 1}
    assert overview["review"]["pending"] == 1
    assert len(overview["timeline"]) == 7
    assert sum(day["searches"] for day in overview["timeline"]) == 1
    assert any(item["intent"] == "REFUND" for item in overview["intents"])
    assert overview["knowledge_gaps"]


def test_settings_validation_and_persistence(api):

    admin = _setup_admin(api)

    # Auto-send requires SMTP.
    assert api.patch("/admin/settings", headers=admin, json={"auto_send_emails": True}).status_code == 400
    assert api.patch("/admin/settings", headers=admin, json={"scheduler_interval_seconds": 5}).status_code == 400

    ok = api.patch("/admin/settings", headers=admin, json={
        "scheduler_interval_seconds": 600, "mark_as_read": True
    }).json()

    assert ok["settings"]["scheduler_interval_seconds"] == 600
    assert api.app_module.automation_scheduler.interval_seconds == 600
    assert api.app_module.app_db.get_setting("mark_as_read") == "True"

    system = api.get("/admin/system", headers=admin).json()
    assert system["automation"]["scheduler_interval_seconds"] == 600
    assert system["engine"]["documents"] == 2
    assert system["access"]["admins"] == 1


def test_reindex(api):

    admin = _setup_admin(api)
    loads = api.app_module.engine.loads

    result = api.post("/admin/reindex", headers=admin).json()

    assert result["success"] and result["chunks"] > 0
    assert api.app_module.engine.loads == loads + 1
