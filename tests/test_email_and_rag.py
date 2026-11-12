from email.message import EmailMessage

from backend.automation.email_fetcher import EmailFetcher
from backend.automation.email_sender import EmailSender, reply_subject
from backend.automation.automation_service import build_search_query
from backend.intent.intent_detector import IntentDetector
from backend.rag.rag_pipeline import RAGPipeline, strip_citations

from tests.conftest import FakeLLM


def _raw_email(**headers):

    message = EmailMessage()
    message["From"] = headers.pop("From", "Student <student@example.com>")
    message["Subject"] = headers.pop("Subject", "Refund question")
    message["Message-ID"] = headers.pop("Message_ID", "<abc123@mail.example.com>")

    for key, value in headers.items():
        message[key.replace("_", "-")] = value

    message.set_content("What is the refund period?")

    return message.as_bytes()


# ============================================================
# FETCHING
# ============================================================

def test_parse_message_extracts_threading_fields():

    parsed = EmailFetcher().parse_message(
        _raw_email(References="<root@mail.example.com>"),
        uid="42"
    )

    assert parsed["uid"] == "42"
    assert parsed["sender_email"] == "student@example.com"
    assert parsed["message_id"] == "<abc123@mail.example.com>"
    assert parsed["references"] == ["<root@mail.example.com>", "<abc123@mail.example.com>"]
    assert parsed["body"].strip() == "What is the refund period?"
    assert parsed["automated"] is False


def test_automated_mail_is_detected():

    fetcher = EmailFetcher()

    newsletter = fetcher.parse_message(_raw_email(List_Unsubscribe="<mailto:x@y.z>"))
    bounce = fetcher.parse_message(_raw_email(From="MAILER-DAEMON@example.com"))
    auto = fetcher.parse_message(_raw_email(Auto_Submitted="auto-replied"))

    assert newsletter["automated"] and bounce["automated"] and auto["automated"]


def test_fetcher_without_configuration_returns_nothing(monkeypatch):

    monkeypatch.setenv("EMAIL_HOST", "")

    fetcher = EmailFetcher()
    fetcher.email_host = ""

    assert fetcher.fetch_messages() == []
    assert fetcher.mark_as_read(["1"]) == 0


# ============================================================
# SENDING
# ============================================================

def test_reply_subject():

    assert reply_subject("Refund") == "Re: Refund"
    assert reply_subject("RE: Refund") == "RE: Refund"
    assert reply_subject("") == "Response to your query"


def test_reply_is_threaded_under_original():

    sender = EmailSender()
    sender.smtp_username = "support@example.com"

    message = sender.build_message(
        "student@example.com",
        "Re: Refund",
        "Hello",
        in_reply_to="<abc123@mail.example.com>",
        references=["<root@mail.example.com>"]
    )

    assert message["In-Reply-To"] == "<abc123@mail.example.com>"
    assert message["References"] == "<root@mail.example.com> <abc123@mail.example.com>"
    assert message["Message-ID"].endswith("@example.com>")


def test_send_without_smtp_configuration_raises():

    sender = EmailSender()
    sender.smtp_username = None

    assert not sender.is_configured()

    try:
        sender.send_email("a@b.c", "s", "b")
    except ValueError as e:
        assert "SMTP_USERNAME" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_build_search_query_drops_quoted_history():

    body = (
        "Hi, how long is the refund period?\n"
        "\n"
        "On Mon, 3 Nov 2026 at 10:00, Support <support@x.com> wrote:\n"
        "> previous answer about certificates\n"
    )

    query = build_search_query("Re: Refund", body)

    assert "refund period" in query
    assert "certificates" not in query
    assert not query.startswith("Re:")


# ============================================================
# RAG
# ============================================================

def _sources():

    return [
        {"id": 1, "text": "Refunds are allowed within 7 days.", "source": "refund.pdf", "page": 1, "cross_score": 6.0},
        {"id": 2, "text": "Refund requests need the enrollment email.", "source": "refund.pdf", "page": 2, "cross_score": 2.0},
        {"id": 3, "text": "Unrelated python content.", "source": "python.pdf", "page": 1, "cross_score": -9.0}
    ]


def _rag(**kwargs):

    return RAGPipeline(llm=FakeLLM(**kwargs), intent_detector=IntentDetector(use_classifier=False))


def test_strip_citations():

    assert strip_citations("Seven days [1]. Email needed [2, 3].") == "Seven days. Email needed."


def test_context_uses_numbered_relevant_sources_only():

    rag = _rag()

    intent, sources, context = rag.prepare("refund period?", _sources())

    assert [s["id"] for s in sources] == [1, 2]       # -9.0 source dropped
    assert context.startswith("[1] (refund.pdf, page 1)")
    assert "[2] (refund.pdf, page 2)" in context
    assert intent["intent"] == "REFUND"


def test_no_results_skips_llm():

    rag = _rag()

    response = rag.generate_answer("anything", [])

    assert rag.llm.calls == 0
    assert response["routing"]["route"] == "HUMAN_REVIEW"


def test_stream_answer_event_order_and_final_answer():

    rag = _rag(answer="Refunds are allowed within 7 days [1].")

    events = list(rag.stream_answer("What is the refund period?", _sources()))

    assert events[0]["type"] == "sources"
    assert all(e["type"] == "token" for e in events[1:-1])
    assert events[-1]["type"] == "done"
    assert "".join(e["text"] for e in events[1:-1]) == events[-1]["answer"]
    assert events[-1]["routing"]["route"] == "AUTO_REPLY"
