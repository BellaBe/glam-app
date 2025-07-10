# services/webhook-service/src/handlers/base.py
"""Base webhook handler interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, NamedTuple
from dataclasses import dataclass

from shared.utils.logger import ServiceLogger


@dataclass
class WebhookData:
    """Parsed webhook data"""

    topic: str
    merchant_id: Optional[str]
    shop_domain: Optional[str]
    idempotency_key: str
    payload: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class DomainEvent:
    """Domain event to publish"""

    event_type: str
    payload: Dict[str, Any]


class WebhookHandler(ABC):
    """Base class for webhook handlers"""

    def __init__(self, logger: Optional[ServiceLogger] = None):
        self.logger = logger or ServiceLogger(__name__)

    @abstractmethod
    def parse_webhook(
        self, body: Dict[str, Any], topic: Optional[str], headers: Dict[str, str]
    ) -> WebhookData:
        """Parse webhook into structured data"""
        pass

    @abstractmethod
    def get_idempotency_key(
        self, body: Dict[str, Any], topic: str, headers: Dict[str, str]
    ) -> str:
        """Generate idempotency key for deduplication"""
        pass

    @abstractmethod
    def map_to_domain_event(self, webhook_data: WebhookData) -> Optional[DomainEvent]:
        """Map webhook to domain event"""
        pass
