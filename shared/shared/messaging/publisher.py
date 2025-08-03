# shared/shared/messaging/publisher.py
"""Publisher base class for domain events and commands."""
import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Optional, TypeVar
from uuid import uuid4

from shared.utils.logger import ServiceLogger
from shared.api.correlation import get_correlation_id
from .jetstream_client import JetStreamClient

DataT = TypeVar("DataT")


class Publisher(ABC):
    """Publishes domain facts (evt.*) - commands to be added when needed."""

    @property
    @abstractmethod
    def service_name(self) -> str: ...
    
    def __init__(self, jetstream_client: JetStreamClient, logger: ServiceLogger) -> None:
        self.js_client = jetstream_client
        self.logger = logger
        self._stream_ready = False

    # ────────────────────────────────────────────────────────────────────────
    async def _ensure_stream(self) -> None:
        if self._stream_ready:
            return
        await self.js_client.ensure_stream(
            name="GLAM_EVENTS",
            subjects=["evt.*", "cmd.*"],
            max_age=24 * 60 * 60,
            max_msgs=1_000_000,
        )
        self._stream_ready = True

    # ────────────────────────────────────────────────────────────────────────
    async def publish_event(
        self,
        subject: str,
        data: dict,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, dict]] = None,
    ) -> str:
        
        if not (subject.startswith("evt.") or subject.startswith("cmd.")):
            raise ValueError("subject must start with 'evt.' or 'cmd.'")
        
        
        await self._ensure_stream()

        event_id = str(uuid4())
        correlation_id = correlation_id #TODO: figure out how to get correlation_id from context
        

        envelope = {
            "event_id": event_id,
            "event_type": subject,
            "correlation_id": correlation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_service": self.service_name,
            "data": data,
            "metadata": metadata or {},
        }


        await self.js_client.js.publish(subject, json.dumps(envelope).encode())
        self.logger.info("Published %s [%s]", subject, event_id)
        return event_id
