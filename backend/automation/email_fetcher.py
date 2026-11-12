import imaplib
import email

from email.header import decode_header
from email.message import Message
from email.utils import parseaddr

from dotenv import load_dotenv
from bs4 import BeautifulSoup

import os


load_dotenv()


class EmailFetcher:

    def __init__(self):

        # ----------------------------------------------------
        # Email configuration
        # ----------------------------------------------------

        self.email_host = os.getenv(
            "EMAIL_HOST",
            ""
        )

        self.email_port = int(
            os.getenv(
                "EMAIL_PORT",
                "993"
            )
        )

        self.email_username = os.getenv(
            "EMAIL_USERNAME",
            ""
        )

        self.email_password = os.getenv(
            "EMAIL_PASSWORD",
            ""
        )

        self.email_folder = os.getenv(
            "EMAIL_FOLDER",
            "INBOX"
        )

        # Mark processed emails as read in Gmail (opt-in).
        self.mark_processed_as_read = (
            os.getenv("EMAIL_MARK_AS_READ", "false").strip().lower()
            in ("1", "true", "yes")
        )

        self.email_limit = int(
            os.getenv(
                "EMAIL_LIMIT",
                "10"
            )
        )

        # ----------------------------------------------------
        # Local test messages
        # ----------------------------------------------------

        self.messages = []

    # ========================================================
    # ADD TEST MESSAGE
    # ========================================================

    def add_message(
        self,
        sender,
        subject,
        body
    ):

        message = {
            "uid": None,
            "message_id": "",
            "references": [],
            "sender": sender,
            "sender_email": parseaddr(sender)[1],
            "subject": subject,
            "body": body,
            "automated": False
        }

        self.messages.append(
            message
        )

        return message

    # ========================================================
    # FETCH REAL EMAILS
    # ========================================================

    def _connect(self, readonly=True):
        """
        Open an IMAP connection and select the configured folder.
        Returns the connection, or None when it is not configured.
        """

        if not (self.email_host and self.email_username and self.email_password):
            print("Email account is not configured (EMAIL_HOST / EMAIL_USERNAME / EMAIL_PASSWORD).")
            return None

        mail = imaplib.IMAP4_SSL(self.email_host, self.email_port)
        mail.login(self.email_username, self.email_password)

        status, _ = mail.select(self.email_folder, readonly=readonly)

        if status != "OK":
            try:
                mail.logout()
            except Exception:
                pass
            raise RuntimeError(f"Unable to select email folder {self.email_folder!r}.")

        return mail

    def parse_message(self, raw_email, uid=None):
        """
        Convert raw RFC 822 bytes into the message dictionary used by
        the automation pipeline.
        """

        message = email.message_from_bytes(raw_email)

        sender = self._decode_subject(message.get("From", ""))
        _, sender_email = parseaddr(sender)

        references = " ".join(
            part for part in (
                message.get("References", ""),
                message.get("In-Reply-To", "")
            ) if part
        ).split()

        message_id = (message.get("Message-ID") or "").strip()

        # Keep References unique and include the message itself so a
        # reply joins the existing thread.
        thread_references = list(dict.fromkeys(
            references + ([message_id] if message_id else [])
        ))

        return {
            "uid": uid,
            "message_id": message_id,
            "references": thread_references,
            "sender": sender,
            "sender_email": sender_email,
            "subject": self._decode_subject(message.get("Subject", "")),
            "body": self._extract_body(message),
            "automated": self._is_automated(message, sender_email),
        }

    def _is_automated(self, message, sender_email):
        """
        True for newsletters, notifications, bounces and other
        machine-generated mail that must never get an automatic reply.
        """

        auto_submitted = (message.get("Auto-Submitted") or "no").strip().lower()

        if auto_submitted != "no":
            return True

        precedence = (message.get("Precedence") or "").strip().lower()

        if precedence in ("bulk", "list", "junk", "auto_reply"):
            return True

        if message.get("List-Unsubscribe") or message.get("List-Id"):
            return True

        local_part = (sender_email or "").split("@")[0].lower()

        automated_senders = (
            "noreply", "no-reply", "donotreply", "do-not-reply",
            "mailer-daemon", "postmaster", "notifications", "notification",
            "newsletter", "bounce"
        )

        if any(token in local_part for token in automated_senders):
            return True

        # Never answer our own messages.
        if sender_email and sender_email.lower() == self.email_username.lower():
            return True

        return False

    def fetch_messages(self):

        # Local test messages take priority (used by scripts/tests).
        if self.messages:
            return self.messages

        mail = None

        try:

            print("Connecting to email server...")

            mail = self._connect(readonly=True)

            if mail is None:
                return []

            status, data = mail.uid("search", None, "UNSEEN")

            if status != "OK":
                print("Unable to search emails.")
                return []

            uids = data[0].split()[-self.email_limit:]

            messages = []

            for uid in uids:

                # BODY.PEEK[] reads the message without marking it read.
                status, message_data = mail.uid("fetch", uid, "(BODY.PEEK[])")

                if status != "OK":
                    continue

                raw_email = next(
                    (part[1] for part in message_data if isinstance(part, tuple)),
                    None
                )

                if raw_email is None:
                    continue

                messages.append(
                    self.parse_message(raw_email, uid=uid.decode())
                )

            print(f"Unread emails fetched: {len(messages)}")

            return messages

        except Exception as e:

            print("Email fetching error:", str(e))

            return []

        finally:

            if mail is not None:
                try:
                    mail.logout()
                except Exception:
                    pass

    def mark_as_read(self, uids):
        """
        Flag the given message UIDs as read (Seen). Returns the number of
        messages marked. Failures are logged, never raised.
        """

        uids = [str(uid) for uid in uids if uid]

        if not uids or self.messages:
            return 0

        mail = None

        try:

            mail = self._connect(readonly=False)

            if mail is None:
                return 0

            status, _ = mail.uid("store", ",".join(uids), "+FLAGS", r"(\Seen)")

            return len(uids) if status == "OK" else 0

        except Exception as e:

            print("Could not mark emails as read:", str(e))

            return 0

        finally:

            if mail is not None:
                try:
                    mail.logout()
                except Exception:
                    pass

    # ========================================================
    # DECODE SUBJECT
    # ========================================================

    def _decode_subject(
        self,
        subject
    ):

        decoded_parts = []

        for part, encoding in decode_header(
            subject
        ):

            if isinstance(
                part,
                bytes
            ):

                try:

                    decoded_parts.append(
                        part.decode(
                            encoding
                            or "utf-8",
                            errors="replace"
                        )
                    )

                except Exception:

                    decoded_parts.append(
                        part.decode(
                            "utf-8",
                            errors="replace"
                        )
                    )

            else:

                decoded_parts.append(
                    str(part)
                )

        return "".join(
            decoded_parts
        )

    # ========================================================
    # EXTRACT EMAIL BODY
    # ========================================================

    def _extract_body(
        self,
        message: Message
    ):

        plain_text = ""
        html_text = ""

        # ----------------------------------------------------
        # Multipart email
        # ----------------------------------------------------

        if message.is_multipart():

            for part in message.walk():

                content_type = (
                    part.get_content_type()
                )

                disposition = (
                    str(
                        part.get(
                            "Content-Disposition",
                            ""
                        )
                    )
                )

                # ------------------------------------------------
                # Ignore attachments
                # ------------------------------------------------

                if (
                    "attachment"
                    in disposition.lower()
                ):

                    continue

                payload = (
                    part.get_payload(
                        decode=True
                    )
                )

                if not payload:

                    continue

                charset = (
                    part.get_content_charset()
                    or "utf-8"
                )

                try:

                    decoded_payload = (
                        payload.decode(
                            charset,
                            errors="replace"
                        )
                    )

                except Exception:

                    decoded_payload = (
                        payload.decode(
                            "utf-8",
                            errors="replace"
                        )
                    )

                # ------------------------------------------------
                # Prefer plain text
                # ------------------------------------------------

                if content_type == "text/plain":

                    plain_text = (
                        decoded_payload
                    )

                # ------------------------------------------------
                # Store HTML as fallback
                # ------------------------------------------------

                elif content_type == "text/html":

                    html_text = (
                        decoded_payload
                    )

        else:

            # ------------------------------------------------
            # Non-multipart email
            # ------------------------------------------------

            payload = (
                message.get_payload(
                    decode=True
                )
            )

            if payload:

                charset = (
                    message.get_content_charset()
                    or "utf-8"
                )

                try:

                    decoded_payload = (
                        payload.decode(
                            charset,
                            errors="replace"
                        )
                    )

                except Exception:

                    decoded_payload = (
                        payload.decode(
                            "utf-8",
                            errors="replace"
                        )
                    )

                if (
                    message.get_content_type()
                    == "text/html"
                ):

                    html_text = (
                        decoded_payload
                    )

                else:

                    plain_text = (
                        decoded_payload
                    )

        # ----------------------------------------------------
        # Use plain text when available
        # ----------------------------------------------------

        if plain_text.strip():

            # ------------------------------------------------
            # Some emails incorrectly label HTML as
            # text/plain. Detect and clean it.
            # ------------------------------------------------

            if self._looks_like_html(
                plain_text
            ):

                return self._html_to_text(
                    plain_text
                )

            return plain_text.strip()

        # ----------------------------------------------------
        # Fall back to HTML
        # ----------------------------------------------------

        if html_text.strip():

            return self._html_to_text(
                html_text
            )

        return ""

    # ========================================================
    # DETECT HTML
    # ========================================================

    def _looks_like_html(
        self,
        text
    ):

        html_markers = [
            "<html",
            "<body",
            "<table",
            "<div",
            "<p>",
            "<a ",
            "<span",
            "<td",
            "<tr"
        ]

        text_lower = text.lower()

        return any(
            marker in text_lower
            for marker in html_markers
        )

    # ========================================================
    # CONVERT HTML TO CLEAN TEXT
    # ========================================================

    def _html_to_text(
        self,
        html_content
    ):

        soup = BeautifulSoup(
            html_content,
            "html.parser"
        )

        # ----------------------------------------------------
        # Remove scripts and styles
        # ----------------------------------------------------

        for element in soup(
            [
                "script",
                "style",
                "noscript"
            ]
        ):

            element.decompose()

        # ----------------------------------------------------
        # Extract readable text
        # ----------------------------------------------------

        text = soup.get_text(
            separator="\n"
        )

        # ----------------------------------------------------
        # Clean excessive whitespace
        # ----------------------------------------------------

        lines = []

        for line in text.splitlines():

            line = line.strip()

            if line:

                lines.append(
                    line
                )

        return "\n".join(
            lines
        )

    # ========================================================
    # CLEAR TEST MESSAGES
    # ========================================================

    def clear_messages(self):

        self.messages = []