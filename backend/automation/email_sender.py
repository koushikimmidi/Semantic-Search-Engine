import os
import smtplib
from email.message import EmailMessage
from email.utils import make_msgid, parseaddr


def reply_subject(subject):
    """
    "Refund" -> "Re: Refund"; "Re: Refund" stays as it is.
    """

    subject = (subject or "").strip()

    if not subject:
        return "Response to your query"

    if subject.lower().startswith("re:"):
        return subject

    return f"Re: {subject}"


class EmailSender:

    def __init__(self):

        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")

    def is_configured(self):

        return bool(self.smtp_username and self.smtp_password)

    def build_message(
        self,
        recipient,
        subject,
        body,
        in_reply_to=None,
        references=None
    ):
        """
        Build the email. When `in_reply_to` (the original
        Message-ID) is given, In-Reply-To and References headers are
        set so mail clients show the reply in the same thread.
        """

        message = EmailMessage()

        message["From"] = self.smtp_username or ""
        message["To"] = recipient
        message["Subject"] = subject

        domain = (parseaddr(self.smtp_username or "")[1].split("@") + ["localhost"])[1]
        message["Message-ID"] = make_msgid(domain=domain or None)

        if in_reply_to:

            message["In-Reply-To"] = in_reply_to

            chain = list(references or [])

            if in_reply_to not in chain:
                chain.append(in_reply_to)

            message["References"] = " ".join(chain)

        message.set_content(body)

        return message

    def send_email(
        self,
        recipient,
        subject,
        body,
        in_reply_to=None,
        references=None
    ):

        if not self.smtp_username:
            raise ValueError("SMTP_USERNAME is not configured.")

        if not self.smtp_password:
            raise ValueError("SMTP_PASSWORD is not configured.")

        if not recipient:
            raise ValueError("The email has no recipient.")

        message = self.build_message(
            recipient,
            subject,
            body,
            in_reply_to=in_reply_to,
            references=references
        )

        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(message)

        return {
            "success": True,
            "sent": True,
            "recipient": recipient,
            "subject": subject,
            "message_id": message["Message-ID"],
            "threaded": bool(in_reply_to)
        }
