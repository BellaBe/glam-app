# shared/events/base.py
from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Any, TypeVar, Generic
from datetime import datetime
from uuid import UUID
from enum import Enum

from .context import EventContext

# Generic type for event data
TData = TypeVar("TData", bound=BaseModel)


class Streams(str, Enum):
    """JetStream streams organized by domain"""
    
    # Core Business Domains
    CATALOG = "CATALOG"               # Catalog management
    MERCHANT = "MERCHANT"             # Merchant management
    BILLING = "BILLING"               # Billing management
    CREDIT = "CREDIT"                 # Credit management
    
    # User & Identity
    AUTH = "AUTH"                     # Authentication & authorization
    PROFILE = "PROFILE"               # Merchant users profiles
    
    # Platform Services
    NOTIFICATION = "NOTIFICATION"     # Notification delivery
    ANALYTICS = "ANALYTICS"           # Analytics and reporting
    WEBHOOKS = "WEBHOOKS"            # Webhook delivery
    SCHEDULER = "SCHEDULER"           # Scheduled jobs
    RATE_LIMIT = "RATE_LIMIT"        # Rate limiting events
    
    # AI Services
    AI_PROCESSING = "AI_PROCESSING"   # AI/ML processing tasks


class EventWrapper(BaseModel, Generic[TData]):
    """Base wrapper for all events with context support"""
    subject: str
    idempotency_key: Optional[str] = None
    
    # Context fields
    event_id: Optional[str] = None
    correlation_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Data field is now generic
    data: TData
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }

    @classmethod
    def from_context(
        cls,
        context: EventContext,
        data: TData,
        subject: Optional[str] = None
    ) -> "EventWrapper[TData]":
        """Create EventWrapper from EventContext and data"""
        if not subject:
            subject = context.event_type
            
        return cls(
            subject=subject,
            idempotency_key=context.idempotency_key,
            event_id=context.event_id,
            correlation_id=context.correlation_id,
            timestamp=context.timestamp,
            metadata=context.metadata,
            data=data
        )
    
    def to_event_dict(self) -> Dict[str, Any]:
        """Convert to event dictionary for publishing"""
        return {
            'event_id': self.event_id,
            'event_type': self.subject,
            'correlation_id': self.correlation_id,
            'idempotency_key': self.idempotency_key,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'metadata': self.metadata or {},
            'payload': self.data.model_dump() if isinstance(self.data, BaseModel) else {}
        }