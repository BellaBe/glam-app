# shared/messaging/models.py
"""Standardized event models for GLAM messaging system."""

from datetime import UTC, datetime
from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Type variable for payload data
T = TypeVar("T", bound=BaseModel)


class PlatformContext(BaseModel):
    """Platform identification context - REQUIRED for all events."""

    merchant_id: UUID = Field(..., description="Internal merchant identifier")
    platform_name: str = Field(..., description="Platform type: shopify, woocommerce, etc")
    platform_shop_id: str = Field(..., description="Platform-specific ID (shop_gid for Shopify)")
    domain: str = Field(..., description="Full platform domain")

    @field_validator("merchant_id", mode="before")
    @classmethod
    def coerce_merchant_id(cls, v):
        """Convert string UUID to UUID object"""
        if isinstance(v, str):
            return UUID(v)
        return v


class BaseEventPayload(BaseModel):
    """
    Base class for all event payloads.
    Services should extend this for their specific events.
    """

    model_config = ConfigDict(json_encoders={UUID: str, datetime: lambda v: v.isoformat()})
    platform: PlatformContext = Field(..., description="Complete platform identification")


class EventEnvelope(BaseModel, Generic[T]):
    """
    Standard envelope for all events in GLAM_EVENTS stream.
    Source service is encoded in the event_type subject.
    """

    model_config = ConfigDict(json_encoders={UUID: str, datetime: lambda v: v.isoformat()})

    # Required envelope fields
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str = Field(..., description="Subject: evt.{service}.{action}.v1")
    correlation_id: str = Field(..., description="Request correlation ID")
    source_service: str = Field(..., description="Service name (redundant with subject)")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="When published to stream")

    # Typed payload with platform context
    data: T = Field(..., description="Event payload extending BaseEventPayload")

    def to_bytes(self) -> bytes:
        """Serialize to JSON bytes for NATS."""
        return self.model_dump_json().encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes) -> "EventEnvelope":
        """Deserialize from NATS message."""
        return cls.model_validate_json(data)


class ErrorPayload(BaseEventPayload):
    """Payload for error/failure events."""

    error_code: str
    error_message: str
    failed_operation: str
    retry_count: int = 0
    max_retries: int = 3
    original_data: dict[str, Any] | None = None
