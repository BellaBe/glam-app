# services/notification-service/src/providers/mailhog_provider.py
import smtplib
import uuid
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from shared.utils.logger import ServiceLogger

from .base import EmailMessage, EmailProvider


class MailhogProvider(EmailProvider):
    """Mailhog SMTP provider for local testing"""

    def __init__(
        self,
        smtp_host: str = "localhost",
        smtp_port: int = 1025,
        logger: ServiceLogger = None,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.logger = logger

    @property
    def name(self) -> str:
        return "mailhog"

    async def send(self, message: EmailMessage) -> dict:  # ✅ Return dict
        """Send email via Mailhog SMTP"""
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = message.subject
        msg["From"] = message.from_email or "noreply@glamyouup.com"
        msg["To"] = message.to

        # Generate a message ID
        message_id = f"mailhog-{uuid.uuid4().hex[:12]}"
        msg["Message-ID"] = f"<{message_id}@glamyouup.com>"

        # Add text and HTML parts
        text_part = MIMEText(message.text, "plain")
        html_part = MIMEText(message.html, "html")
        msg.attach(text_part)
        msg.attach(html_part)

        # Send via SMTP
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.send_message(msg)

            if self.logger:
                self.logger.info(
                    "Email sent via Mailhog",
                    extra={
                        "to": message.to,
                        "message_id": message_id,
                        "host": self.smtp_host,
                        "port": self.smtp_port,
                    },
                )

            # ✅ Return dict instead of string
            return {
                "message_id": message_id,
                "provider": self.name,
                "status": "accepted",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            raise Exception(f"Mailhog SMTP error: {e!s}") from e

    async def get_status(self, message_id: str) -> dict[str, Any]:
        """Get message status (always sent for Mailhog)"""
        return {"message_id": message_id, "status": "sent", "provider": self.name}
