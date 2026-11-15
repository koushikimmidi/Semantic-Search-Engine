import json
import os
import shutil
import time
import traceback
from typing import List, Optional

from dotenv import load_dotenv

# Load .env before any module reads configuration from the environment.
load_dotenv()

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import StreamingResponse  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from backend.engine.search_engine import SearchEngine  # noqa: E402
from backend.rag import RAGPipeline  # noqa: E402

from backend.automation.automation_service import AutomationService  # noqa: E402
from backend.automation.automation_runner import AutomationRunner  # noqa: E402
from backend.automation.automation_scheduler import AutomationScheduler  # noqa: E402
from backend.automation.automation_history import AutomationHistory  # noqa: E402
from backend.automation.escalation import EscalationManager  # noqa: E402

from backend.storage import AppDatabase  # noqa: E402
from backend.accounts import AccountError, TokenSigner, UserStore  # noqa: E402
from backend.analytics import EventStore, build_overview  # noqa: E402
from backend.api import auth  # noqa: E402
from backend.api.auth import auth_enabled, get_principal, require_role  # noqa: E402


app = FastAPI(
    title="Semantic Intent Search Engine",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# CONFIGURATION
# ============================================================

KNOWLEDGE_BASE_PATH = os.getenv("KNOWLEDGE_BASE_PATH", "data/documents/education")
AUTOMATION_DATA_DIR = os.getenv("AUTOMATION_DATA_DIR", "data/automation")
KNOWLEDGE_BASE_ROOT = os.path.realpath(KNOWLEDGE_BASE_PATH)

SUPPORTED_EXTENSIONS = (".txt", ".pdf", ".docx", ".md")

# Real email replies are opt-in. Keep "false" until SMTP is configured.
SEND_EMAILS = (
    os.getenv("AUTOMATION_SEND_EMAILS", "false").strip().lower()
    in ("1", "true", "yes")
)

SCHEDULER_INTERVAL_SECONDS = int(os.getenv("AUTOMATION_INTERVAL_SECONDS", "300"))


def resolve_kb_path(relative_path):
    """
    Resolve a user-supplied relative path inside the knowledge base.

    Returns the absolute path, or None when the path escapes the
    knowledge base (e.g. "../x", "/etc/x", "C:/Windows/x").
    """

    relative_path = (relative_path or "").replace("\\", "/").strip()

    if not relative_path:
        return None

    full_path = os.path.realpath(os.path.join(KNOWLEDGE_BASE_ROOT, relative_path))

    try:
        inside = os.path.commonpath([full_path, KNOWLEDGE_BASE_ROOT]) == KNOWLEDGE_BASE_ROOT
    except ValueError:
        # Different drives on Windows.
        return None

    if not inside or full_path == KNOWLEDGE_BASE_ROOT:
        return None

    return full_path


# ============================================================
# ACCOUNTS, AUDIT LOG & ANALYTICS
# ============================================================

app_db = AppDatabase(os.getenv("APP_DB_PATH") or os.path.join(AUTOMATION_DATA_DIR, "app.db"))
user_store = UserStore(app_db)
token_signer = TokenSigner(secret_file=os.path.join(AUTOMATION_DATA_DIR, "auth_secret.key"))
event_store = EventStore(app_db)

auth.configure(user_store, token_signer)

if not auth_enabled():
    print(
        "WARNING: no user accounts and no API keys are configured. "
        "Authentication is DISABLED; every request has admin rights. "
        "Set ADMIN_API_KEY in .env and create the admin account in the UI."
    )


# ============================================================
# ENGINE & AUTOMATION
# ============================================================

engine = SearchEngine(KNOWLEDGE_BASE_PATH)
engine.load()

rag = RAGPipeline()

automation_service = AutomationService(
    search_engine=engine,
    rag_pipeline=rag,
    send_emails=SEND_EMAILS,
    escalation_manager=EscalationManager(storage_directory=AUTOMATION_DATA_DIR),
    event_store=event_store
)

automation_runner = AutomationRunner(
    send_emails=SEND_EMAILS,
    automation_service=automation_service,
    state_directory=AUTOMATION_DATA_DIR
)

automation_scheduler = AutomationScheduler(
    interval_seconds=SCHEDULER_INTERVAL_SECONDS,
    send_emails=SEND_EMAILS,
    automation_runner=automation_runner
)

automation_history = AutomationHistory(history_directory=AUTOMATION_DATA_DIR)


# ============================================================
# RUNTIME SETTINGS (admin can change them; stored in app.db)
# ============================================================

def _truthy(value):

    return str(value).strip().lower() in ("1", "true", "yes", "on")


def apply_settings():

    auto_send = app_db.get_setting("auto_send_emails")

    if auto_send is not None:
        enabled = _truthy(auto_send)
        automation_service.send_emails = enabled
        automation_runner.send_emails = enabled
        automation_scheduler.send_emails = enabled

    interval = app_db.get_setting("scheduler_interval_seconds")

    if interval is not None:
        automation_scheduler.interval_seconds = int(interval)

    mark_read = app_db.get_setting("mark_as_read")

    if mark_read is not None:
        automation_runner.email_fetcher.mark_processed_as_read = _truthy(mark_read)


def current_settings():

    return {
        "auto_send_emails": automation_service.send_emails,
        "scheduler_interval_seconds": automation_scheduler.interval_seconds,
        "mark_as_read": automation_runner.email_fetcher.mark_processed_as_read
    }


apply_settings()


# ============================================================
# REQUEST MODELS
# ============================================================

class SearchRequest(BaseModel):
    query: str


class AutomationMessage(BaseModel):
    sender: str
    subject: str
    body: str


class EscalationResolution(BaseModel):
    resolution_note: Optional[str] = None


class EscalationReply(BaseModel):
    reply: str
    resolution_note: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class SetupRequest(BaseModel):
    setup_key: str
    username: str
    password: str
    full_name: Optional[str] = ""


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = "employee"
    full_name: Optional[str] = ""


class UpdateUserRequest(BaseModel):
    role: Optional[str] = None
    active: Optional[bool] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class SettingsRequest(BaseModel):
    auto_send_emails: Optional[bool] = None
    scheduler_interval_seconds: Optional[int] = None
    mark_as_read: Optional[bool] = None


def _error(message, status_code=400):

    raise HTTPException(status_code=status_code, detail=message)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "message": "Semantic Intent Search Engine API",
        "version": app.version,
        "knowledge_base": "education"
    }


# ============================================================
# AUTHENTICATION
# ============================================================

@app.get("/auth/status")
def auth_status():
    """Public: tells the UI whether to show first-time setup or login."""

    return {
        "success": True,
        "setup_required": user_store.count() == 0,
        "setup_available": bool((os.getenv("ADMIN_API_KEY") or "").strip()),
        "auth_enabled": auth_enabled()
    }


@app.post("/auth/setup")
def auth_setup(request: SetupRequest):
    """
    First-time setup: create the first admin account. Proves
    ownership with ADMIN_API_KEY from .env and only works while no
    accounts exist.
    """

    expected = (os.getenv("ADMIN_API_KEY") or "").strip()

    if user_store.count() > 0:
        _error("Setup is already complete. Please sign in.", 409)

    if not expected:
        _error("Set ADMIN_API_KEY in the backend .env file, restart the backend, then try again.")

    if request.setup_key.strip() != expected:
        event_store.audit({"username": request.username, "role": "anonymous"}, "setup_failed")
        _error("The setup key does not match ADMIN_API_KEY in .env.", 403)

    try:
        user = user_store.create(request.username, request.password, "admin", request.full_name)
    except AccountError as e:
        _error(str(e))

    user = user_store.record_login(user["id"])

    event_store.audit({"username": user["username"], "role": "admin"}, "setup_admin_created", user["username"])

    return {
        "success": True,
        "token": token_signer.create(user["id"], user["username"], user["role"]),
        "user": user
    }


@app.post("/auth/login")
def auth_login(request: LoginRequest):

    try:
        user = user_store.authenticate(request.username, request.password)
    except AccountError as e:
        event_store.audit({"username": request.username.strip()[:40], "role": "anonymous"}, "login_failed")
        _error(str(e), 401)

    event_store.audit({"username": user["username"], "role": user["role"]}, "login")

    return {
        "success": True,
        "token": token_signer.create(user["id"], user["username"], user["role"]),
        "user": user
    }


@app.get("/auth/me")
def auth_me(principal: dict = Depends(get_principal)):

    return {
        "success": True,
        "role": principal["role"],
        "auth_enabled": auth_enabled(),
        "username": principal["username"],
        "full_name": principal["full_name"],
        "method": principal["method"]
    }


@app.post("/auth/change-password")
def change_password(request: ChangePasswordRequest, principal: dict = Depends(get_principal)):

    if principal["method"] != "account":
        _error("Only signed-in user accounts can change their password.", 403)

    try:
        user_store.change_password(principal["user_id"], request.current_password, request.new_password)
    except AccountError as e:
        _error(str(e))

    event_store.audit(principal, "password_changed", principal["username"])

    return {"success": True}


# ============================================================
# SEARCH
# ============================================================

@app.post("/search")
def search(request: SearchRequest, principal: dict = Depends(get_principal)):

    started = time.perf_counter()

    try:

        results = engine.search(request.query)
        response = rag.generate_answer(request.query, results)
        response["success"] = True

        event_store.log_search(
            principal["username"], request.query, response,
            (time.perf_counter() - started) * 1000
        )

        return response

    except Exception as e:

        traceback.print_exc()

        return {"success": False, "error": str(e)}


@app.post("/search/stream")
def search_stream(request: SearchRequest, principal: dict = Depends(get_principal)):
    """
    Newline-delimited JSON events:
      {"type": "sources", ...}   retrieved sources + intent
      {"type": "token", "text"}  answer text as it is generated
      {"type": "done", ...}      full response with confidence
      {"type": "error", ...}     if something fails mid-stream
    """

    started = time.perf_counter()

    def events():

        try:

            results = engine.search(request.query)

            for event in rag.stream_answer(request.query, results):

                if event.get("type") == "done":
                    event["success"] = True
                    event_store.log_search(
                        principal["username"], request.query, event,
                        (time.perf_counter() - started) * 1000
                    )

                yield json.dumps(event, default=str) + "\n"

        except Exception as e:

            traceback.print_exc()

            yield json.dumps({"type": "error", "success": False, "error": str(e)}) + "\n"

    return StreamingResponse(
        events(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


# ============================================================
# AUTOMATION (employees and admins)
# ============================================================

@app.get("/automation/status", dependencies=[Depends(require_role("agent"))])
def automation_status():

    return {
        "status": "ready",
        "service": "automation",
        "knowledge_base": "education",
        "email_sending": automation_service.send_emails,
        "scheduler": automation_scheduler.status()
    }


@app.post("/automation/process")
def process_automation_message(
    message: AutomationMessage,
    principal: dict = Depends(require_role("agent"))
):

    try:

        result = automation_service.process_message(
            {"sender": message.sender, "subject": message.subject, "body": message.body},
            channel="test"
        )

        event_store.audit(principal, "test_message", message.subject, {"route": result.get("route")})

        return result

    except Exception as e:

        traceback.print_exc()

        return {"success": False, "error": str(e)}


@app.get("/automation/history", dependencies=[Depends(require_role("agent"))])
def automation_history_list():

    records = automation_history.load()

    return {"success": True, "count": len(records), "history": records}


@app.get("/automation/history/latest", dependencies=[Depends(require_role("agent"))])
def automation_history_latest():

    return {"success": True, "history": automation_history.latest()}


@app.get("/automation/dashboard", dependencies=[Depends(require_role("agent"))])
def automation_dashboard():

    records = automation_history.load()

    def total(field):
        return sum(record.get(field, 0) for record in records)

    processed = total("processed")
    failed = total("failed")
    attempted = processed + failed

    return {
        "success": True,
        "dashboard": {
            "total_executions": len(records),
            "total_fetched": total("fetched"),
            "total_processed": processed,
            "total_skipped": total("skipped"),
            "total_auto_reply": total("auto_reply"),
            "total_human_review": total("human_review"),
            "total_failed": failed,
            "success_rate": round(processed / attempted * 100, 2) if attempted else 100.0,
            "latest_execution": automation_history.latest(),
            "scheduler": automation_scheduler.status(),
            "email_sending": automation_service.send_emails,
            "pending_reviews": len(
                automation_service.escalation_manager.get_escalated_messages("PENDING")
            )
        }
    }


@app.get("/automation/scheduler/status", dependencies=[Depends(require_role("agent"))])
def automation_scheduler_status():

    return {"success": True, "status": automation_scheduler.status()}


# ============================================================
# HUMAN REVIEW QUEUE
# ============================================================

@app.get("/automation/escalations", dependencies=[Depends(require_role("agent"))])
def list_escalations(status: Optional[str] = Query(None)):

    records = automation_service.escalation_manager.get_escalated_messages(status)

    return {"success": True, "count": len(records), "escalations": records}


@app.post("/automation/escalations/{escalation_id}/resolve")
def resolve_escalation(
    escalation_id: str,
    resolution: EscalationResolution,
    principal: dict = Depends(require_role("agent"))
):

    record = automation_service.escalation_manager.resolve(
        escalation_id,
        resolution.resolution_note,
        resolved_by=principal["username"]
    )

    if record is None:
        return {"success": False, "error": "Escalation not found"}

    event_store.audit(principal, "escalation_resolved", record.get("subject", ""), {"id": escalation_id})

    return {"success": True, "escalation": record}


@app.post("/automation/escalations/{escalation_id}/reply")
def reply_to_escalation(
    escalation_id: str,
    request: EscalationReply,
    principal: dict = Depends(require_role("agent"))
):

    result = automation_service.send_human_reply(
        escalation_id,
        request.reply,
        request.resolution_note,
        resolved_by=principal["username"]
    )

    if result.get("success"):
        event_store.audit(
            principal, "escalation_replied",
            result["escalation"].get("subject", ""),
            {"id": escalation_id, "to": result["escalation"].get("sender_email")}
        )

    return result


# ============================================================
# ANALYTICS
# ============================================================

@app.get("/analytics/overview", dependencies=[Depends(require_role("agent"))])
def analytics_overview(days: int = Query(30, ge=1, le=365)):

    return {
        "success": True,
        "overview": build_overview(
            event_store,
            automation_service.escalation_manager.get_escalated_messages(),
            automation_history.load(),
            days
        )
    }


# ============================================================
# ADMIN: AUTOMATION CONTROL
# ============================================================

@app.post("/automation/run")
def run_automation(principal: dict = Depends(require_role("admin"))):

    try:

        results = automation_runner.run()
        summary = automation_runner.last_summary

        event_store.audit(principal, "inbox_run", "", summary)

        return {"success": True, "summary": summary, "results": results}

    except Exception as e:

        traceback.print_exc()

        return {"success": False, "error": str(e)}


@app.post("/automation/scheduler/start")
def start_automation_scheduler(principal: dict = Depends(require_role("admin"))):

    started = automation_scheduler.start()

    if started:
        event_store.audit(principal, "scheduler_started", "", automation_scheduler.status())

    return {"success": True, "started": started, "status": automation_scheduler.status()}


@app.post("/automation/scheduler/stop")
def stop_automation_scheduler(principal: dict = Depends(require_role("admin"))):

    stopped = automation_scheduler.stop()

    if stopped:
        event_store.audit(principal, "scheduler_stopped")

    return {"success": True, "stopped": stopped, "status": automation_scheduler.status()}


# ============================================================
# ADMIN: USERS
# ============================================================

@app.get("/admin/users", dependencies=[Depends(require_role("admin"))])
def list_users():

    return {"success": True, "users": user_store.list()}


@app.post("/admin/users")
def create_user(request: CreateUserRequest, principal: dict = Depends(require_role("admin"))):

    try:
        user = user_store.create(request.username, request.password, request.role, request.full_name)
    except AccountError as e:
        _error(str(e))

    event_store.audit(principal, "user_created", user["username"], {"role": user["role"]})

    return {"success": True, "user": user}


@app.patch("/admin/users/{user_id}")
def update_user(user_id: int, request: UpdateUserRequest, principal: dict = Depends(require_role("admin"))):

    try:
        user = user_store.update(
            user_id,
            role=request.role,
            active=request.active,
            full_name=request.full_name,
            password=request.password
        )
    except AccountError as e:
        _error(str(e))

    changes = {k: v for k, v in request.model_dump().items() if v is not None and k != "password"}

    if request.password:
        changes["password"] = "reset"

    event_store.audit(principal, "user_updated", user["username"], changes)

    return {"success": True, "user": user}


@app.delete("/admin/users/{user_id}")
def delete_user(user_id: int, principal: dict = Depends(require_role("admin"))):

    if principal.get("user_id") == user_id:
        _error("You cannot delete your own account.")

    try:
        user = user_store.delete(user_id)
    except AccountError as e:
        _error(str(e))

    event_store.audit(principal, "user_deleted", user["username"])

    return {"success": True}


# ============================================================
# ADMIN: AUDIT LOG
# ============================================================

@app.get("/admin/audit", dependencies=[Depends(require_role("admin"))])
def audit_log(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    action: Optional[str] = Query(None),
    actor: Optional[str] = Query(None)
):

    page = event_store.list_audit(limit, offset, action or None, actor or None)

    return {"success": True, **page, "actions": event_store.list_actions()}


# ============================================================
# ADMIN: SYSTEM & SETTINGS
# ============================================================

def _ollama_status():

    import requests

    host = rag.llm.host if hasattr(rag.llm, "host") else ""

    if not host:
        return {"reachable": False, "model_available": False}

    try:
        response = requests.get(f"{host}/api/tags", timeout=2)
        models = [m.get("name") for m in response.json().get("models", [])]
        return {"reachable": True, "model_available": rag.llm.model in models, "models": models}
    except Exception:
        return {"reachable": False, "model_available": False}


@app.get("/admin/system", dependencies=[Depends(require_role("admin"))])
def system_info():

    from backend.config import Settings

    fetcher = automation_runner.email_fetcher
    confidence = rag.confidence_engine
    users = user_store.list()

    return {
        "success": True,
        "engine": {
            "documents": len(list_documents()),
            "chunks": len(engine.documents or []),
            "embedding_model": Settings.EMBEDDING_MODEL,
            "reranker_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "rerank_candidates": getattr(engine, "rerank_candidates", None),
            "chunk_size": int(os.getenv("CHUNK_SIZE", "700")),
            "intent_classifier": getattr(rag.intent_detector, "use_classifier", False)
        },
        "llm": {
            "model": getattr(rag.llm, "model", ""),
            "host": getattr(rag.llm, "host", ""),
            **_ollama_status()
        },
        "confidence": {
            "very_high_threshold": confidence.very_high_threshold,
            "high_threshold": confidence.high_threshold,
            "minimum_score_gap": confidence.minimum_score_gap,
            "medium_threshold": confidence.medium_threshold
        },
        "automation": {
            **current_settings(),
            "scheduler_running": automation_scheduler.running,
            "smtp_configured": automation_service.email_sender.is_configured(),
            "inbox_configured": bool(fetcher.email_host and fetcher.email_username and fetcher.email_password),
            "inbox_address": fetcher.email_username
        },
        "access": {
            "auth_enabled": auth_enabled(),
            "admins": sum(1 for u in users if u["role"] == "admin" and u["active"]),
            "employees": sum(1 for u in users if u["role"] == "employee" and u["active"]),
            "api_keys": {
                "admin": bool((os.getenv("ADMIN_API_KEY") or "").strip()),
                "agent": bool((os.getenv("AGENT_API_KEY") or "").strip())
            }
        }
    }


@app.patch("/admin/settings")
def update_settings(request: SettingsRequest, principal: dict = Depends(require_role("admin"))):

    changes = {}

    if request.auto_send_emails is not None:

        if request.auto_send_emails and not automation_service.email_sender.is_configured():
            _error("Configure SMTP_USERNAME and SMTP_PASSWORD in .env before turning on automatic replies.")

        app_db.set_setting("auto_send_emails", request.auto_send_emails)
        changes["auto_send_emails"] = request.auto_send_emails

    if request.scheduler_interval_seconds is not None:

        if not 60 <= request.scheduler_interval_seconds <= 86400:
            _error("The check interval must be between 60 seconds and 24 hours.")

        app_db.set_setting("scheduler_interval_seconds", request.scheduler_interval_seconds)
        changes["scheduler_interval_seconds"] = request.scheduler_interval_seconds

    if request.mark_as_read is not None:

        app_db.set_setting("mark_as_read", request.mark_as_read)
        changes["mark_as_read"] = request.mark_as_read

    apply_settings()

    if changes:
        event_store.audit(principal, "settings_changed", "", changes)

    return {"success": True, "settings": current_settings()}


@app.post("/admin/reindex")
def reindex(principal: dict = Depends(require_role("admin"))):

    started = time.perf_counter()

    try:
        engine.load()
    except Exception as e:
        traceback.print_exc()
        return {"success": False, "error": f"Re-indexing failed: {str(e)}"}

    seconds = round(time.perf_counter() - started, 1)

    event_store.audit(principal, "reindex", "", {"chunks": len(engine.documents or []), "seconds": seconds})

    return {"success": True, "chunks": len(engine.documents or []), "seconds": seconds}


# ============================================================
# DOCUMENTS (everyone can browse; admins can change)
# ============================================================

@app.get("/documents")
def list_documents():

    docs = []

    if not os.path.exists(KNOWLEDGE_BASE_ROOT):
        return docs

    for root, _, files in os.walk(KNOWLEDGE_BASE_ROOT):

        for file in files:

            if not file.lower().endswith(SUPPORTED_EXTENSIONS):
                continue

            full_path = os.path.join(root, file)
            stat = os.stat(full_path)

            docs.append({
                "name": file,
                "path": os.path.relpath(full_path, KNOWLEDGE_BASE_ROOT).replace("\\", "/"),
                "size": stat.st_size,
                "modified": stat.st_mtime
            })

    return docs


@app.post("/documents/upload")
def upload_documents(
    files: List[UploadFile] = File(...),
    paths: Optional[List[str]] = Form(None),
    principal: dict = Depends(require_role("admin"))
):

    uploaded = []
    skipped = []

    for i, file in enumerate(files):

        rel_path = (paths[i] if paths and i < len(paths) else file.filename) or ""

        if not rel_path.lower().endswith(SUPPORTED_EXTENSIONS):
            skipped.append(rel_path)
            continue

        # Keep the file inside the KB; fall back to the bare file name.
        dest_path = resolve_kb_path(rel_path) or resolve_kb_path(
            os.path.basename(rel_path.replace("\\", "/"))
        )

        if dest_path is None:
            skipped.append(rel_path)
            continue

        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        uploaded.append(rel_path)

    if uploaded:

        try:
            engine.load()
        except Exception as e:
            print("Error reloading search engine after upload:", e)
            return {"success": False, "error": f"Failed to reload search engine: {str(e)}"}

        event_store.audit(principal, "documents_uploaded", ", ".join(uploaded)[:300], {"count": len(uploaded)})

    return {"success": True, "count": len(uploaded), "skipped": skipped}


@app.get("/documents/content")
def get_document_content(path: str = Query(...)):

    full_path = resolve_kb_path(path)

    if full_path is None:
        return {"success": False, "error": "Invalid file path"}

    if not os.path.isfile(full_path):
        return {"success": False, "error": "File not found"}

    try:
        from backend.loaders import DocumentLoader
        return {"success": True, "content": DocumentLoader().load(full_path)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.delete("/documents")
def delete_document(path: str = Query(...), principal: dict = Depends(require_role("admin"))):

    full_path = resolve_kb_path(path)

    if full_path is None:
        return {"success": False, "error": "Invalid file path"}

    if not os.path.isfile(full_path):
        return {"success": False, "error": "File not found"}

    os.remove(full_path)

    # Clean empty parent directories (never the KB root).
    parent = os.path.dirname(full_path)

    while (
        os.path.normcase(parent) != os.path.normcase(KNOWLEDGE_BASE_ROOT)
        and parent.startswith(KNOWLEDGE_BASE_ROOT)
    ):
        try:
            if os.listdir(parent):
                break
            os.rmdir(parent)
            parent = os.path.dirname(parent)
        except Exception:
            break

    try:
        engine.load()
    except Exception as e:
        print("Error reloading search engine after deletion:", e)
        return {"success": False, "error": f"Failed to reload search engine: {str(e)}"}

    event_store.audit(principal, "document_deleted", path)

    return {"success": True}
