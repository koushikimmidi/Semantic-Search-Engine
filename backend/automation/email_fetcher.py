import imaplib
import email

from email.header import decode_header
from email.message import Message

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

            "sender": sender,

            "subject": subject,

            "body": body

        }

        self.messages.append(
            message
        )

        return message

    # ========================================================
    # FETCH REAL EMAILS
    # ========================================================

    def fetch_messages(self):

        # ----------------------------------------------------
        # If local test messages exist,
        # return them for testing.
        # ----------------------------------------------------

        if self.messages:

            return self.messages

        # ----------------------------------------------------
        # Validate configuration
        # ----------------------------------------------------

        if not self.email_host:

            print(
                "Email host is not configured."
            )

            return []

        if not self.email_username:

            print(
                "Email username is not configured."
            )

            return []

        if not self.email_password:

            print(
                "Email password is not configured."
            )

            return []

        # ----------------------------------------------------
        # Connect to IMAP server
        # ----------------------------------------------------

        mail = None

        try:

            print(
                "Connecting to email server..."
            )

            mail = imaplib.IMAP4_SSL(
                self.email_host,
                self.email_port
            )

            # ------------------------------------------------
            # Login
            # ------------------------------------------------

            mail.login(
                self.email_username,
                self.email_password
            )

            print(
                "Email login successful."
            )

            # ------------------------------------------------
            # Select mailbox in READ-ONLY mode
            # ------------------------------------------------

            status, _ = mail.select(
                self.email_folder,
                readonly=True
            )

            if status != "OK":

                print(
                    "Unable to select email folder."
                )

                return []

            # ------------------------------------------------
            # Search unread messages
            # ------------------------------------------------

            status, data = mail.search(
                None,
                "UNSEEN"
            )

            if status != "OK":

                print(
                    "Unable to search emails."
                )

                return []

            email_ids = data[0].split()

            # ------------------------------------------------
            # Limit number of emails
            # ------------------------------------------------

            email_ids = email_ids[
                -self.email_limit:
            ]

            messages = []

            # ------------------------------------------------
            # Read emails
            # ------------------------------------------------

            for email_id in email_ids:

                status, message_data = (
                    mail.fetch(
                        email_id,
                        "(RFC822)"
                    )
                )

                if status != "OK":

                    continue

                raw_email = None

                for part in message_data:

                    if isinstance(
                        part,
                        tuple
                    ):

                        raw_email = part[1]

                        break

                if raw_email is None:

                    continue

                message = (
                    email.message_from_bytes(
                        raw_email
                    )
                )

                sender = (
                    message.get(
                        "From",
                        ""
                    )
                )

                subject = (
                    self._decode_subject(
                        message.get(
                            "Subject",
                            ""
                        )
                    )
                )

                body = (
                    self._extract_body(
                        message
                    )
                )

                messages.append(
                    {
                        "sender": sender,
                        "subject": subject,
                        "body": body
                    }
                )

            print(
                f"Unread emails fetched: "
                f"{len(messages)}"
            )

            return messages

        except Exception as e:

            print(
                "Email fetching error:",
                str(e)
            )

            return []

        finally:

            # ------------------------------------------------
            # Close connection safely
            # ------------------------------------------------

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