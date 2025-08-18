# services/notification-service/src/providers/sendgrid_provider.py
from typing import Any

import httpx

from shared.utils.logger import ServiceLogger

from .base import EmailMessage, EmailProvider


class SendGridProvider(EmailProvider):
    """SendGrid email provider"""

    def __init__(
        self,
        api_key: str,
        from_email: str,
        from_name: str,
        sandbox_mode: bool = False,
        logger: ServiceLogger = None,
    ):
        self.api_key = api_key
        self.from_email = from_email
        self.from_name = from_name
        self.sandbox_mode = sandbox_mode
        self.logger = logger
        self.base_url = "https://api.sendgrid.com/v3"

    @property
    def name(self) -> str:
        return "sendgrid"

    async def send(self, message: EmailMessage) -> str:
        """Send email via SendGrid API"""
        async with httpx.AsyncClient() as client:
            payload = {
                "personalizations": [{"to": [{"email": message.to}], "subject": message.subject}],
                "from": {
                    "email": message.from_email or self.from_email,
                    "name": message.from_name or self.from_name,
                },
                "content": [
                    {"type": "text/plain", "value": message.text},
                    {"type": "text/html", "value": message.html},
                ],
            }

            # Add sandbox mode for testing
            if self.sandbox_mode:
                payload["mail_settings"] = {"sandbox_mode": {"enable": True}}

            # Add custom metadata if provided
            if message.metadata:
                payload["custom_args"] = message.metadata

            response = await client.post(
                f"{self.base_url}/mail/send",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code not in (200, 202):
                error_data = response.json() if response.content else {}
                raise Exception(f"SendGrid API error: {response.status_code} - {error_data}")

            # Extract message ID from headers
            message_id = response.headers.get("X-Message-Id", "")

            if self.logger:
                self.logger.info(
                    "Email sent via SendGrid",
                    extra={
                        "to": message.to,
                        "message_id": message_id,
                        "sandbox": self.sandbox_mode,
                    },
                )

            return message_id

    async def get_status(self, message_id: str) -> dict[str, Any]:
        """Get message status from SendGrid"""
        # Implementation would query SendGrid's Activity API
        # For MVP, return basic status
        return {"message_id": message_id, "status": "sent", "provider": self.name}
