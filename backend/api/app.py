from fastapi import FastAPI, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import shutil
from typing import List, Optional

from dotenv import load_dotenv

# Load .env before any module reads configuration from the environment.
load_dotenv()

from backend.engine.search_engine import SearchEngine
from backend.rag import RAGPipeline

from backend.automation.automation_service import AutomationService
from backend.automation.automation_runner import AutomationRunner
from backend.automation.automation_scheduler import AutomationScheduler
from backend.automation.automation_history import AutomationHistory


app = FastAPI(
    title="Semantic Intent Search Engine",
    version="1.0.0"
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# EDUCATION KNOWLEDGE BASE
# ============================================================

KNOWLEDGE_BASE_PATH = "data/documents/education"

KNOWLEDGE_BASE_ROOT = os.path.realpath(KNOWLEDGE_BASE_PATH)

SUPPORTED_EXTENSIONS = (
    ".txt",
    ".pdf",
    ".docx",
    ".md"
)

# Real email replies are opt-in. Keep "false" until SMTP is configured.
SEND_EMAILS = (
    os.getenv("AUTOMATION_SEND_EMAILS", "false").strip().lower()
    in ("1", "true", "yes")
)

SCHEDULER_INTERVAL_SECONDS = int(
    os.getenv("AUTOMATION_INTERVAL_SECONDS", "300")
)


def resolve_kb_path(relative_path):
    """
    Resolve a user-supplied relative path inside the knowledge base.

    Returns the absolute path, or None when the path escapes the
    knowledge base (e.g. "../x", "/etc/x", "C:/Windows/x").
    """

    relative_path = (relative_path or "").replace("\\", "/").strip()

    if not relative_path:
        return None

    full_path = os.path.realpath(
        os.path.join(KNOWLEDGE_BASE_ROOT, relative_path)
    )

    try:
        inside = (
            os.path.commonpath([full_path, KNOWLEDGE_BASE_ROOT])
            == KNOWLEDGE_BASE_ROOT
        )
    except ValueError:
        # Different drives on Windows.
        return None

    if not inside or full_path == KNOWLEDGE_BASE_ROOT:
        return None

    return full_path


# ============================================================
# SEARCH ENGINE
# ============================================================

engine = SearchEngine(
    KNOWLEDGE_BASE_PATH
)

engine.load()


# ============================================================
# RAG PIPELINE
# ============================================================

rag = RAGPipeline()


# ============================================================
# AUTOMATION SERVICE
#
# Reuse the already-loaded SearchEngine and RAGPipeline.
# ============================================================

automation_service = AutomationService(
    search_engine=engine,
    rag_pipeline=rag,
    send_emails=SEND_EMAILS
)

# ------------------------------------------------------------
# AUTOMATION RUNNER
#
# Reuse the already-loaded AutomationService so the API does
# not create a second SearchEngine/RAG pipeline.
# ------------------------------------------------------------

automation_runner = AutomationRunner(
    send_emails=SEND_EMAILS,
    automation_service=automation_service
)

# ------------------------------------------------------------
# AUTOMATION SCHEDULER
#
# Reuse the already-loaded AutomationRunner. The scheduler
# starts in stopped state and can be controlled through the API.
# ------------------------------------------------------------

automation_scheduler = AutomationScheduler(
    interval_seconds=SCHEDULER_INTERVAL_SECONDS,
    send_emails=SEND_EMAILS,
    automation_runner=automation_runner
)

# ------------------------------------------------------------
# AUTOMATION HISTORY
#
# Reuse the same persistent history file used by
# AutomationRunner.
# ------------------------------------------------------------

automation_history = AutomationHistory()


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


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "message": "Semantic Intent Search Engine API",
        "knowledge_base": "education"
    }


# ============================================================
# AUTOMATION STATUS
# ============================================================

@app.get("/automation/status")
def automation_status():

    return {

        "status": "ready",

        "service": "automation",

        "knowledge_base": "education",

        "email_sending": (
            automation_service.send_emails
        ),

        "scheduler": automation_scheduler.status()

    }


# ============================================================
# SEARCH
# ============================================================

@app.post("/search")
def search(request: SearchRequest):

    try:

        print("=" * 60)
        print("Received Query:", request.query)
        print("=" * 60)

        # ----------------------------------------------------
        # Semantic Search
        # ----------------------------------------------------

        results = engine.search(
            request.query
        )

        print(
            f"Found {len(results)} search results."
        )

        # ----------------------------------------------------
        # RAG Pipeline
        # ----------------------------------------------------

        response = rag.generate_answer(
            request.query,
            results
        )

        print(
            "Generated response successfully."
        )

        response["success"] = True

        return response

    except Exception as e:

        import traceback

        print("\n========== ERROR ==========")

        traceback.print_exc()

        print("===========================\n")

        return {
            "success": False,
            "error": str(e)
        }


# ============================================================
# AUTOMATION PROCESS
# ============================================================

@app.post("/automation/process")
def process_automation_message(
    message: AutomationMessage
):

    try:

        print("=" * 60)
        print("AUTOMATION REQUEST")
        print("=" * 60)

        print(
            "Sender:",
            message.sender
        )

        print(
            "Subject:",
            message.subject
        )

        print(
            "Body:",
            message.body
        )

        # ----------------------------------------------------
        # Convert Pydantic model to dictionary
        # ----------------------------------------------------

        message_data = {

            "sender": message.sender,

            "subject": message.subject,

            "body": message.body

        }

        # ----------------------------------------------------
        # Process through AutomationService
        # ----------------------------------------------------

        result = automation_service.process_message(
            message_data
        )

        print(
            "Automation route:",
            result.get("route")
        )

        print("=" * 60)

        return result

    except Exception as e:

        import traceback

        print(
            "\n========== AUTOMATION ERROR =========="
        )

        traceback.print_exc()

        print(
            "======================================\n"
        )

        return {
            "success": False,
            "error": str(e)
        }


# ============================================================
# AUTOMATION RUN
# ============================================================

@app.post("/automation/run")
def run_automation():

    try:

        print("=" * 60)
        print("AUTOMATION RUN REQUEST")
        print("=" * 60)

        # ----------------------------------------------------
        # Run real Gmail automation
        # ----------------------------------------------------

        results = automation_runner.run()

        summary = automation_runner.last_summary

        print(
            "Automation summary:",
            summary
        )

        print("=" * 60)

        return {
            "success": True,
            "summary": summary,
            "results": results
        }

    except Exception as e:

        import traceback

        print(
            "\n========== AUTOMATION RUN ERROR =========="
        )

        traceback.print_exc()

        print(
            "==========================================\n"
        )

        return {
            "success": False,
            "error": str(e)
        }


# ============================================================
# AUTOMATION HISTORY
# ============================================================

@app.get("/automation/history")
def automation_history_list():

    try:

        records = automation_history.load()

        return {
            "success": True,
            "count": len(records),
            "history": records
        }

    except Exception as e:

        import traceback

        print(
            "\n========== AUTOMATION HISTORY ERROR =========="
        )

        traceback.print_exc()

        print(
            "==============================================\n"
        )

        return {
            "success": False,
            "error": str(e)
        }


@app.get("/automation/history/latest")
def automation_history_latest():

    try:

        latest = automation_history.latest()

        return {
            "success": True,
            "history": latest
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


# ============================================================
# AUTOMATION DASHBOARD
# ============================================================

@app.get("/automation/dashboard")
def automation_dashboard():

    try:

        records = automation_history.load()

        total_executions = len(records)

        total_fetched = sum(
            record.get(
                "fetched",
                0
            )
            for record in records
        )

        total_processed = sum(
            record.get(
                "processed",
                0
            )
            for record in records
        )

        total_skipped = sum(
            record.get(
                "skipped",
                0
            )
            for record in records
        )

        total_auto_reply = sum(
            record.get(
                "auto_reply",
                0
            )
            for record in records
        )

        total_human_review = sum(
            record.get(
                "human_review",
                0
            )
            for record in records
        )

        total_failed = sum(
            record.get(
                "failed",
                0
            )
            for record in records
        )

        total_attempted = (
            total_processed
            + total_failed
        )

        if total_attempted > 0:

            success_rate = (
                total_processed
                / total_attempted
            ) * 100

        else:

            success_rate = 100.0

        latest_execution = (
            automation_history.latest()
        )

        return {

            "success": True,

            "dashboard": {

                "total_executions": (
                    total_executions
                ),

                "total_fetched": (
                    total_fetched
                ),

                "total_processed": (
                    total_processed
                ),

                "total_skipped": (
                    total_skipped
                ),

                "total_auto_reply": (
                    total_auto_reply
                ),

                "total_human_review": (
                    total_human_review
                ),

                "total_failed": (
                    total_failed
                ),

                "success_rate": round(
                    success_rate,
                    2
                ),

                "latest_execution": (
                    latest_execution
                ),

                "scheduler": (
                    automation_scheduler.status()
                ),

                "email_sending": (
                    automation_service.send_emails
                ),

                "pending_reviews": len(
                    automation_service.escalation_manager
                    .get_escalated_messages("PENDING")
                )
            }
        }

    except Exception as e:

        import traceback

        print(
            "\n========== DASHBOARD ERROR =========="
        )

        traceback.print_exc()

        print(
            "=====================================\n"
        )

        return {

            "success": False,

            "error": str(e)

        }


# ============================================================
# AUTOMATION SCHEDULER
# ============================================================

@app.post("/automation/scheduler/start")
def start_automation_scheduler():

    try:

        started = automation_scheduler.start()

        return {
            "success": True,
            "started": started,
            "status": automation_scheduler.status()
        }

    except Exception as e:

        import traceback

        print(
            "\n========== SCHEDULER START ERROR =========="
        )

        traceback.print_exc()

        print(
            "===========================================\n"
        )

        return {
            "success": False,
            "error": str(e)
        }


@app.post("/automation/scheduler/stop")
def stop_automation_scheduler():

    try:

        stopped = automation_scheduler.stop()

        return {
            "success": True,
            "stopped": stopped,
            "status": automation_scheduler.status()
        }

    except Exception as e:

        import traceback

        print(
            "\n========== SCHEDULER STOP ERROR =========="
        )

        traceback.print_exc()

        print(
            "==========================================\n"
        )

        return {
            "success": False,
            "error": str(e)
        }


@app.get("/automation/scheduler/status")
def automation_scheduler_status():

    try:

        return {
            "success": True,
            "status": automation_scheduler.status()
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


# ============================================================
# HUMAN REVIEW QUEUE (ESCALATIONS)
# ============================================================

@app.get("/automation/escalations")
def list_escalations(
    status: Optional[str] = Query(None)
):

    records = (
        automation_service.escalation_manager
        .get_escalated_messages(status)
    )

    return {
        "success": True,
        "count": len(records),
        "escalations": records
    }


@app.post("/automation/escalations/{escalation_id}/resolve")
def resolve_escalation(
    escalation_id: str,
    resolution: EscalationResolution
):

    record = (
        automation_service.escalation_manager
        .resolve(escalation_id, resolution.resolution_note)
    )

    if record is None:

        return {
            "success": False,
            "error": "Escalation not found"
        }

    return {
        "success": True,
        "escalation": record
    }


# ============================================================
# LIST DOCUMENTS
# ============================================================

@app.get("/documents")
def list_documents():

    docs = []

    if not os.path.exists(
        KNOWLEDGE_BASE_ROOT
    ):

        return docs

    for root, _, files in os.walk(
        KNOWLEDGE_BASE_ROOT
    ):

        for file in files:

            if not file.lower().endswith(
                SUPPORTED_EXTENSIONS
            ):

                continue

            full_path = os.path.join(
                root,
                file
            )

            rel_path = os.path.relpath(
                full_path,
                KNOWLEDGE_BASE_ROOT
            ).replace(
                "\\",
                "/"
            )

            stat = os.stat(
                full_path
            )

            docs.append(
                {
                    "name": file,
                    "path": rel_path,
                    "size": stat.st_size,
                    "modified": stat.st_mtime
                }
            )

    return docs


# ============================================================
# UPLOAD DOCUMENTS
# ============================================================

@app.post("/documents/upload")
def upload_documents(
    files: List[UploadFile] = File(...),
    paths: Optional[List[str]] = Form(None)
):

    uploaded_count = 0

    skipped = []

    for i, file in enumerate(files):

        rel_path = (
            paths[i]
            if paths and i < len(paths)
            else file.filename
        ) or ""

        # ----------------------------------------------------
        # Only supported document types
        # ----------------------------------------------------

        if not rel_path.lower().endswith(
            SUPPORTED_EXTENSIONS
        ):

            skipped.append(rel_path)

            continue

        # ----------------------------------------------------
        # Security check: keep the file inside the KB.
        # Fall back to the bare file name if the path escapes.
        # ----------------------------------------------------

        dest_path = resolve_kb_path(rel_path)

        if dest_path is None:

            dest_path = resolve_kb_path(
                os.path.basename(
                    rel_path.replace("\\", "/")
                )
            )

        if dest_path is None:

            skipped.append(rel_path)

            continue

        os.makedirs(
            os.path.dirname(dest_path),
            exist_ok=True
        )

        with open(
            dest_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        uploaded_count += 1

    # --------------------------------------------------------
    # Reload Search Engine
    # --------------------------------------------------------

    if uploaded_count:

        try:

            engine.load()

        except Exception as e:

            print(
                "Error reloading search engine after upload:",
                e
            )

            return {
                "success": False,
                "error": (
                    "Failed to reload search engine: "
                    f"{str(e)}"
                )
            }

    return {
        "success": True,
        "count": uploaded_count,
        "skipped": skipped
    }


# ============================================================
# GET DOCUMENT CONTENT
# ============================================================

@app.get("/documents/content")
def get_document_content(
    path: str = Query(...)
):

    full_path = resolve_kb_path(path)

    if full_path is None:

        return {
            "success": False,
            "error": "Invalid file path"
        }

    if not os.path.isfile(full_path):

        return {
            "success": False,
            "error": "File not found"
        }

    try:

        from backend.loaders import DocumentLoader

        text = DocumentLoader().load(
            full_path
        )

        return {
            "success": True,
            "content": text
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


# ============================================================
# DELETE DOCUMENT
# ============================================================

@app.delete("/documents")
def delete_document(
    path: str = Query(...)
):

    full_path = resolve_kb_path(path)

    if full_path is None:

        return {
            "success": False,
            "error": "Invalid file path"
        }

    if not os.path.isfile(full_path):

        return {
            "success": False,
            "error": "File not found"
        }

    os.remove(
        full_path
    )

    # --------------------------------------------------------
    # Clean empty parent directories (never the KB root)
    # --------------------------------------------------------

    parent = os.path.dirname(
        full_path
    )

    while (
        os.path.normcase(parent)
        != os.path.normcase(KNOWLEDGE_BASE_ROOT)
        and parent.startswith(KNOWLEDGE_BASE_ROOT)
    ):

        try:

            if os.listdir(parent):
                break

            os.rmdir(parent)

            parent = os.path.dirname(
                parent
            )

        except Exception:

            break

    # --------------------------------------------------------
    # Reload Search Engine
    # --------------------------------------------------------

    try:

        engine.load()

    except Exception as e:

        print(
            "Error reloading search engine after deletion:",
            e
        )

        return {
            "success": False,
            "error": (
                "Failed to reload search engine: "
                f"{str(e)}"
            )
        }

    return {
        "success": True
    }
