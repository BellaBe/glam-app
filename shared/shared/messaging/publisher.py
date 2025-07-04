# File: shared/shared/messaging/publisher.py
import json
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from nats.aio.client import Client
from nats.js import JetStreamContext
from nats.js.api import StreamConfig, RetentionPolicy, StorageType


class JetStreamEventPublisher(ABC):
    """
    JetStream publisher specifically for structured events.
    Combines base functionality with event structure in one class.
    """

    @property
    @abstractmethod
    def stream_name(self) -> str:
        """The JetStream stream name to publish to."""
        pass

    @property
    @abstractmethod
    def subjects(self) -> list[str]:
        """List of subjects this stream should handle."""
        pass

    @property
    @abstractmethod
    def service_name(self) -> str:
        """The name of the service publishing events."""
        pass

    @property
    def service_version(self) -> str:
        """The version of the service."""
        return "1.0.0"

    def __init__(self, client: Client, js: JetStreamContext, logger: Optional[Any] = None):
        self.client = client
        self.js = js
        self._stream_created = False
        self.logger = logger or self._get_default_logger()

    def _get_default_logger(self):
        """Get a default logger if none provided"""
        import logging
        return logging.getLogger(self.__class__.__name__)
    
    async def ensure_stream(self) -> None:
        """Ensure the stream exists with default configuration."""
        if self._stream_created:
            return

        stream_config = StreamConfig(
            name=self.stream_name,
            subjects=self.subjects,
            retention=RetentionPolicy.LIMITS,
            max_age=7 * 24 * 60 * 60,  # 7 days
            max_msgs_per_subject=100000,
            storage=StorageType.FILE,
            duplicate_window=60,
            allow_rollup_hdrs=True,
        )

        try:
            await self.js.stream_info(self.stream_name)
            if self.logger:
                self.logger.info(f"Using existing stream: {self.stream_name}")
        except:
            await self.js.add_stream(stream_config)
            if self.logger:
                self.logger.info(f"Created new stream: {self.stream_name}")

        self._stream_created = True

    async def publish_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        subject: Optional[str] = None,
        correlation_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish a structured event."""
        await self.ensure_stream()

        # Generate IDs
        event_id = str(uuid.uuid4())
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        if not idempotency_key:
            idempotency_key = event_id

        # Build event
        event = {
            "event_id": event_id,
            "event_type": event_type,
            "correlation_id": correlation_id,
            "idempotency_key": idempotency_key,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "source_service": self.service_name,
                "version": self.service_version,
                **(metadata or {})
            },
            "payload": payload
        }

        # Publish
        subject = subject or event_type
        headers = {"Nats-Msg-Id": idempotency_key}
        
        try:
            ack = await self.js.publish(
                subject,
                json.dumps(event).encode("utf-8"),
                headers=headers
            )
            if self.logger:
                self.logger.debug(f"Published {event_type} to {subject} (seq: {ack.seq})")
                
            if ack.duplicate:
                self.logger.info(
                    f"Duplicate message detected and ignored",
                    extra={"idempotency_key": idempotency_key}
                )
            return event_id
        
        except Exception as e:
            if self.logger:
                self.logger.critical(f"Failed to publish to {subject}: {e}", exc_info=True)
            raise

    async def publish_command(self, command_type: str, payload: Dict[str, Any], **kwargs) -> str:
        """Publish a command event."""
        if not command_type.startswith('cmd.'):
            command_type = f'cmd.{command_type}'
        
        idempotency_key = kwargs.pop('idempotency_key', None)

        return await self.publish_event(event_type=command_type, payload=payload, idempotency_key=idempotency_key, **kwargs)

    
    async def publish_event_response(self, event_type: str, payload: Dict[str, Any], **kwargs) -> str:
        """Publish an event response."""
        if not event_type.startswith('evt.'):
            event_type = f'evt.{event_type}'
            
        # Ensure idempotency key is set
        idempotency_key = kwargs.pop('idempotency_key', None)
        
        return await self.publish_event(event_type=event_type, payload=payload, idempotency_key=idempotency_key, **kwargs)


