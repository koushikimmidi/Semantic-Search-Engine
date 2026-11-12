import re

from backend.engine.search_engine import SearchEngine
from backend.rag.rag_pipeline import RAGPipeline, strip_citations
from backend.llm.gemma import FALLBACK_ANSWER
from backend.automation.message_router import MessageRouter
from backend.automation.email_sender import EmailSender, reply_subject
from backend.automation.escalation import EscalationManager
from backend.automation.email_fetcher import EmailFetcher


SKIPPED = "SKIPPED"

_QUOTED_REPLY_START = re.compile(
    r"^\s*(on .{3,200} wrote:|-{2,}\s*original message\s*-{2,}|from:\s.+)$",
    re.IGNORECASE
)


def build_search_query(subject, body, max_length=1000):
    """
    Turn an email into a search query: drop quoted earlier messages
    ("> ..." lines and everything after "On ... wrote:"), add the
    subject for context, and cap the length.
    """

    lines = []

    for line in (body or "").splitlines():

        if _QUOTED_REPLY_START.match(line):
            break

        if line.lstrip().startswith(">"):
            continue

        lines.append(line.strip())

    text = " ".join(line for line in lines if line)

    subject = (subject or "").strip()

    if subject.lower().startswith("re:"):
        subject = subject[3:].strip()

    if subject and subject.lower() not in text.lower():
        text = f"{subject}. {text}" if text else subject

    return text[:max_length].strip()


class AutomationService:

    def __init__(
        self,
        knowledge_base_path="data/documents/education",
        send_emails=False,
        search_engine=None,
        rag_pipeline=None,
        email_fetcher=None,
        escalation_manager=None,
        email_sender=None
    ):

        self.send_emails = send_emails

        # Reuse loaded components when given (FastAPI does this so
        # models are loaded once).
        if search_engine is not None:
            self.search_engine = search_engine
        else:
            self.search_engine = SearchEngine(knowledge_base_path)
            self.search_engine.load()

        self.rag = rag_pipeline if rag_pipeline is not None else RAGPipeline()

        self.router = MessageRouter()

        self.email_sender = email_sender or EmailSender()

        self.escalation_manager = escalation_manager or EscalationManager()

        self.email_fetcher = email_fetcher or EmailFetcher()

    # ========================================================
    # HELPERS
    # ========================================================

    def _escalate(self, message, confidence, reason, answer, intent):

        # The fallback sentence is not a useful draft for an agent.
        suggested = strip_citations(answer)

        if not suggested or FALLBACK_ANSWER.lower() in suggested.lower():
            suggested = None

        return self.escalation_manager.escalate(
            message,
            confidence,
            reason,
            suggested_answer=suggested,
            intent=intent
        )

    def _send_reply(self, message, body):

        return self.email_sender.send_email(
            recipient=message.get("sender_email") or message.get("sender", ""),
            subject=reply_subject(message.get("subject", "")),
            body=body,
            in_reply_to=message.get("message_id") or None,
            references=message.get("references") or None
        )

    # ========================================================
    # PROCESS MESSAGE
    # ========================================================

    def process_message(
        self,
        message
    ):

        if not message:
            return {
                "success": False,
                "error": "No message was provided."
            }

        subject = message.get("subject", "") or ""
        body = message.get("body", "") or ""

        if not body.strip() and not subject.strip():
            return {
                "success": False,
                "error": "Message body is empty."
            }

        # Newsletters, notifications, bounces: never answer them.
        if message.get("automated"):
            return {
                "success": True,
                "route": SKIPPED,
                "message": message,
                "reason": "Automated or bulk email; no reply is sent."
            }

        query = build_search_query(subject, body) or body

        search_results = self.search_engine.search(query)

        rag_result = self.rag.generate_answer(query, search_results)

        answer = rag_result.get("answer", "")
        intent = rag_result.get("intent")
        confidence = rag_result.get("confidence")
        sources = rag_result.get("sources", [])

        routing = self.router.route(confidence)
        route = routing.get("route")

        # Emails do not show the source list, so drop [1] markers.
        email_answer = strip_citations(answer)

        # ----------------------------------------------------
        # AUTO REPLY
        # ----------------------------------------------------

        if route == self.router.AUTO_REPLY:

            if self.send_emails:

                try:

                    email_result = self._send_reply(message, email_answer)

                except Exception as e:

                    # A failed send must not crash processing; a
                    # human follows up instead.
                    print("Email sending failed:", str(e))

                    email_result = {
                        "success": False,
                        "sent": False,
                        "reason": f"Email sending failed: {str(e)}"
                    }

                    return {
                        "success": True,
                        "route": self.router.HUMAN_REVIEW,
                        "message": message,
                        "answer": answer,
                        "intent": intent,
                        "confidence": confidence,
                        "sources": sources,
                        "email": email_result,
                        "escalation": self._escalate(
                            message, confidence,
                            "Automatic reply could not be sent.",
                            answer, intent
                        )
                    }

            else:

                email_result = {
                    "success": False,
                    "sent": False,
                    "reason": (
                        "Email sending is disabled because the "
                        "service is running in safe test mode."
                    )
                }

            return {
                "success": True,
                "route": self.router.AUTO_REPLY,
                "message": message,
                "answer": answer,
                "email_body": email_answer,
                "intent": intent,
                "confidence": confidence,
                "sources": sources,
                "email": email_result
            }

        # ----------------------------------------------------
        # HUMAN REVIEW
        # ----------------------------------------------------

        return {
            "success": True,
            "route": self.router.HUMAN_REVIEW,
            "message": message,
            "answer": answer,
            "intent": intent,
            "confidence": confidence,
            "sources": sources,
            "escalation": self._escalate(
                message, confidence, routing.get("reason"), answer, intent
            )
        }

    # ========================================================
    # HUMAN REPLY FROM THE REVIEW QUEUE
    # ========================================================

    def send_human_reply(self, escalation_id, reply_text, agent_note=None):
        """
        Send an agent-approved reply for a queued message (threaded
        under the original email) and mark the item resolved.
        """

        reply_text = (reply_text or "").strip()

        if not reply_text:
            return {"success": False, "error": "The reply is empty."}

        item = self.escalation_manager.get(escalation_id)

        if item is None:
            return {"success": False, "error": "Escalation not found"}

        if item.get("status") != EscalationManager.PENDING:
            return {"success": False, "error": "This message was already handled."}

        if not self.email_sender.is_configured():
            return {
                "success": False,
                "error": (
                    "SMTP is not configured. Set SMTP_USERNAME and "
                    "SMTP_PASSWORD in .env to send replies."
                )
            }

        try:
            email_result = self._send_reply(item, reply_text)
        except Exception as e:
            return {"success": False, "error": f"Email sending failed: {str(e)}"}

        record = self.escalation_manager.resolve(
            escalation_id,
            agent_note or "Replied by support agent.",
            reply=reply_text
        )

        return {"success": True, "email": email_result, "escalation": record}

    # ========================================================
    # PROCESS INBOX
    # ========================================================

    def process_inbox(self):

        messages = self.email_fetcher.fetch_messages()

        if not messages:
            return {"success": True, "processed": 0, "results": []}

        results = [self.process_message(message) for message in messages]

        return {
            "success": True,
            "processed": len(messages),
            "auto_reply": sum(1 for r in results if r.get("route") == self.router.AUTO_REPLY),
            "human_review": sum(1 for r in results if r.get("route") == self.router.HUMAN_REVIEW),
            "failed": sum(1 for r in results if not r.get("success")),
            "results": results
        }
