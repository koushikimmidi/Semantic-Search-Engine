from backend.engine.search_engine import SearchEngine
from backend.rag.rag_pipeline import RAGPipeline
from backend.automation.message_router import MessageRouter
from backend.automation.email_sender import EmailSender
from backend.automation.escalation import EscalationManager
from backend.automation.email_fetcher import EmailFetcher


class AutomationService:

    def __init__(
        self,
        knowledge_base_path="data/documents/education",
        send_emails=False,
        search_engine=None,
        rag_pipeline=None,
        email_fetcher=None
    ):

        # ----------------------------------------------------
        # Configuration
        # ----------------------------------------------------

        self.send_emails = send_emails

        # ----------------------------------------------------
        # Search Engine
        #
        # Reuse an existing SearchEngine when provided.
        # Otherwise create one for standalone usage.
        # ----------------------------------------------------

        if search_engine is not None:

            self.search_engine = search_engine

        else:

            self.search_engine = SearchEngine(
                knowledge_base_path
            )

            self.search_engine.load()

        # ----------------------------------------------------
        # RAG Pipeline
        #
        # Reuse an existing RAGPipeline when provided.
        # ----------------------------------------------------

        if rag_pipeline is not None:

            self.rag = rag_pipeline

        else:

            self.rag = RAGPipeline()

        # ----------------------------------------------------
        # Message Router
        # ----------------------------------------------------

        self.router = MessageRouter()

        # ----------------------------------------------------
        # Email Sender
        # ----------------------------------------------------

        self.email_sender = EmailSender()

        # ----------------------------------------------------
        # Escalation Manager
        # ----------------------------------------------------

        self.escalation_manager = EscalationManager()

        # ----------------------------------------------------
        # Email Fetcher
        #
        # Reuse an existing EmailFetcher when provided.
        # Otherwise create one for standalone usage.
        # ----------------------------------------------------

        if email_fetcher is not None:

            self.email_fetcher = email_fetcher

        else:

            self.email_fetcher = EmailFetcher()

    # ========================================================
    # PROCESS MESSAGE
    # ========================================================

    def process_message(
        self,
        message
    ):

        # ----------------------------------------------------
        # Validate message
        # ----------------------------------------------------

        if not message:

            return {
                "success": False,
                "error": "No message was provided."
            }

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

        if not body.strip():

            return {
                "success": False,
                "error": "Message body is empty."
            }

        # ----------------------------------------------------
        # Semantic Search
        # ----------------------------------------------------

        search_results = self.search_engine.search(
            body
        )

        # ----------------------------------------------------
        # RAG + Intent + Confidence
        # ----------------------------------------------------

        rag_result = self.rag.generate_answer(
            body,
            search_results
        )

        answer = rag_result.get(
            "answer",
            ""
        )

        intent = rag_result.get(
            "intent"
        )

        confidence = rag_result.get(
            "confidence"
        )

        # ----------------------------------------------------
        # Route message
        # ----------------------------------------------------

        routing = self.router.route(
            confidence
        )

        route = routing.get(
            "route"
        )

        # ----------------------------------------------------
        # AUTO REPLY
        # ----------------------------------------------------

        if route == self.router.AUTO_REPLY:

            email_result = None

            # ------------------------------------------------
            # Safe mode
            # ------------------------------------------------

            if self.send_emails:

                # A failed send must not crash processing; the
                # message is escalated so a human can follow up.
                try:

                    email_result = self.email_sender.send_email(

                        recipient=sender,

                        subject=(
                            "Re: "
                            + subject
                            if subject
                            else
                            "Response to your query"
                        ),

                        body=answer

                    )

                except Exception as e:

                    print("Email sending failed:", str(e))

                    email_result = {
                        "success": False,
                        "sent": False,
                        "reason": f"Email sending failed: {str(e)}"
                    }

                    escalation = self.escalation_manager.escalate(
                        message,
                        confidence,
                        "Automatic reply could not be sent.",
                        suggested_answer=answer,
                        intent=intent
                    )

                    return {
                        "success": True,
                        "route": self.router.HUMAN_REVIEW,
                        "message": message,
                        "answer": answer,
                        "intent": intent,
                        "confidence": confidence,
                        "email": email_result,
                        "escalation": escalation
                    }

            else:

                email_result = {

                    "success": False,

                    "sent": False,

                    "reason": (
                        "Email sending is disabled "
                        "because the service is running "
                        "in safe test mode."
                    )

                }

            return {

                "success": True,

                "route": self.router.AUTO_REPLY,

                "message": message,

                "answer": answer,

                "intent": intent,

                "confidence": confidence,

                "email": email_result

            }

        # ----------------------------------------------------
        # HUMAN REVIEW
        # ----------------------------------------------------

        escalation = (
            self.escalation_manager.escalate(
                message,
                confidence,
                routing.get("reason"),
                suggested_answer=answer,
                intent=intent
            )
        )

        return {

            "success": True,

            "route": self.router.HUMAN_REVIEW,

            "message": message,

            "answer": answer,

            "intent": intent,

            "confidence": confidence,

            "escalation": escalation

        }

    # ========================================================
    # PROCESS INBOX
    # ========================================================

    def process_inbox(self):

        # ----------------------------------------------------
        # Fetch messages
        # ----------------------------------------------------

        messages = self.email_fetcher.fetch_messages()

        # ----------------------------------------------------
        # Validate fetched messages
        # ----------------------------------------------------

        if not messages:

            return {

                "success": True,

                "processed": 0,

                "results": []

            }

        # ----------------------------------------------------
        # Process every message
        # ----------------------------------------------------

        results = []

        for message in messages:

            result = self.process_message(
                message
            )

            results.append(
                result
            )

        # ----------------------------------------------------
        # Count routes
        # ----------------------------------------------------

        auto_reply_count = sum(

            1

            for result in results

            if result.get("route")
            == self.router.AUTO_REPLY

        )

        human_review_count = sum(

            1

            for result in results

            if result.get("route")
            == self.router.HUMAN_REVIEW

        )

        failed_count = sum(

            1

            for result in results

            if not result.get("success")

        )

        # ----------------------------------------------------
        # Return inbox processing summary
        # ----------------------------------------------------

        return {

            "success": True,

            "processed": len(messages),

            "auto_reply": auto_reply_count,

            "human_review": human_review_count,

            "failed": failed_count,

            "results": results

        }