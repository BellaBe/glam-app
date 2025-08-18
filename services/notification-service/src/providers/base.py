# services/notification-service/src/providers/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class EmailMessage:
    """Email message structure"""

    to: str
    subject: str
    html: str
    text: str
    from_email: str | None = None
    from_name: str | None = None
    metadata: dict[str, Any] | None = None


class EmailProvider(ABC):
    """Base email provider interface"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass

    @abstractmethod
    async def send(self, message: EmailMessage) -> str:
        """
        Send email and return provider message ID

        Raises:
            Exception: On send failure
        """
        pass

    @abstractmethod
    async def get_status(self, message_id: str) -> dict[str, Any]:
        """Get message status from provider"""
        pass
