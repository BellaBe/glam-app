# services/notification-service/src/providers/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class EmailMessage:
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
    async def send(self, message: EmailMessage) -> dict[str, Any]:  # ✅ Must return dict
        """Send email and return response dict with at least 'message_id' key"""
        pass

    @abstractmethod
    async def get_status(self, message_id: str) -> dict[str, Any]:
        """Get message status"""
        pass
