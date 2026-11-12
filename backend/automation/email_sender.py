import os
import smtplib

from email.message import EmailMessage


class EmailSender:

    def __init__(self):

        self.smtp_host = os.getenv(
            "SMTP_HOST",
            "smtp.gmail.com"
        )

        self.smtp_port = int(
            os.getenv(
                "SMTP_PORT",
                "587"
            )
        )

        self.smtp_username = os.getenv(
            "SMTP_USERNAME"
        )

        self.smtp_password = os.getenv(
            "SMTP_PASSWORD"
        )

    def send_email(
        self,
        recipient,
        subject,
        body
    ):

        # ----------------------------------------------------
        # Validate SMTP configuration
        # ----------------------------------------------------

        if not self.smtp_username:
            raise ValueError(
                "SMTP_USERNAME is not configured."
            )

        if not self.smtp_password:
            raise ValueError(
                "SMTP_PASSWORD is not configured."
            )

        # ----------------------------------------------------
        # Create email
        # ----------------------------------------------------

        message = EmailMessage()

        message["From"] = self.smtp_username
        message["To"] = recipient
        message["Subject"] = subject

        message.set_content(
            body
        )

        # ----------------------------------------------------
        # Connect to SMTP server
        # ----------------------------------------------------

        with smtplib.SMTP(
            self.smtp_host,
            self.smtp_port
        ) as server:

            server.starttls()

            server.login(
                self.smtp_username,
                self.smtp_password
            )

            server.send_message(
                message
            )

        # ----------------------------------------------------
        # Return status
        # ----------------------------------------------------

        return {
            "success": True,
            "recipient": recipient,
            "subject": subject
        }