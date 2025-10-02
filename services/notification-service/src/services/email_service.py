# services/notification-service/src/services/email_service.py
from typing import Any

from shared.utils.logger import ServiceLogger

from ..providers.base import EmailMessage, EmailProvider


class EmailService:
    """Service for sending emails through providers"""

    def __init__(self, provider: EmailProvider, logger: ServiceLogger = None):
        self.provider = provider
        self.logger = logger

    @property
    def provider_name(self) -> str:
        """Get current provider name"""
        return self.provider.name

    async def send(self, to: str, subject: str, html: str, text: str, metadata: dict[str, Any] | None = None) -> str:
        """
        Send email through configured provider

        Returns:
            Provider message ID

        Raises:
            Exception: On send failure
        """
        message = EmailMessage(to=to, subject=subject, html=html, text=text, metadata=metadata)

        try:
            response = await self.provider.send(message)

            if self.logger:
                self.logger.info(
                    "Email sent successfully",
                    extra={
                        "provider": self.provider_name,
                        "to": to,
                        "subject": subject,
                        "message_id": response.get("message_id"),
                    },
                )

            return response

        except Exception as e:
            if self.logger:
                self.logger.exception(
                    f"Email send failed: {e!s}",
                    extra={"provider": self.provider_name, "to": to, "subject": subject, "error": str(e)},
                )
            raise

    async def get_status(self, message_id: str) -> dict[str, Any]:
        """Get message status from provider"""
        return await self.provider.get_status(message_id)
