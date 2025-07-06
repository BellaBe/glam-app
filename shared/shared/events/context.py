# shared/events/context.py
"""
Standardized event context management for all services.

Provides consistent context handling for event-driven architecture.
"""

from typing import Dict, Any, Optional, TypeVar, Generic
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from ..api.correlation import set_correlation_context, get_correlation_context

T = TypeVar('T')


@dataclass
class EventContext:
    """Standard context for all events across the platform"""
    event_id: str
    event_type: str
    correlation_id: Optional[str]
    timestamp: datetime
    source_service: str
    idempotency_key: Optional[str] = None
    version: str = "1.0"
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @classmethod
    def from_event(cls, event: Dict[str, Any]) -> "EventContext":
        """Extract context from incoming event"""
        return cls(
            event_id=event.get('event_id', ''),
            event_type=event.get('event_type', ''),
            correlation_id=event.get('correlation_id'),
            timestamp=datetime.fromisoformat(
                event.get('timestamp', datetime.now(timezone.utc).isoformat())
            ),
            source_service=event.get('metadata', {}).get('source_service', 'unknown'),
            idempotency_key=event.get('idempotency_key'),
            version=event.get('metadata', {}).get('version', '1.0'),
            metadata=event.get('metadata', {})
        )
    
    @classmethod
    def create(
        cls,
        event_type: str,
        source_service: str,
        correlation_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "EventContext":
        """Create new event context"""
        # Use existing correlation if available
        if not correlation_id:
            correlation_id = get_correlation_context()
            
        return cls(
            event_id=f"evt_{uuid4().hex[:12]}",
            event_type=event_type,
            correlation_id=correlation_id,
            timestamp=datetime.now(timezone.utc),
            source_service=source_service,
            idempotency_key=idempotency_key,
            version="1.0",
            metadata=metadata or {}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for logging or serialization"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'correlation_id': self.correlation_id,
            'timestamp': self.timestamp.isoformat(),
            'source_service': self.source_service,
            'idempotency_key': self.idempotency_key,
            'version': self.version,
            **(self.metadata or {})
        }
    
    def apply_correlation(self):
        """Apply correlation context to async context"""
        if self.correlation_id:
            set_correlation_context(self.correlation_id)
    
    def create_response_context(
        self,
        response_event_type: str,
        response_service: str,
        idempotency_key: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> "EventContext":
        """Create context for response events, preserving correlation chain"""
        metadata = {
            'triggered_by': self.event_id,
            'original_source': self.source_service,
            **(additional_metadata or {})
        }
        
        return EventContext.create(
            event_type=response_event_type,
            source_service=response_service,
            correlation_id=self.correlation_id,  # Preserve correlation
            idempotency_key=idempotency_key,
            metadata=metadata
        )


@dataclass
class EventPayload(Generic[T]):
    """Wrapper for typed event payloads with context"""
    context: EventContext
    data: T
    
    @property
    def correlation_id(self) -> Optional[str]:
        return self.context.correlation_id
    
    def to_event_dict(self) -> Dict[str, Any]:
        """Convert to event dictionary for publishing"""
        return {
            'event_id': self.context.event_id,
            'event_type': self.context.event_type,
            'correlation_id': self.context.correlation_id,
            'idempotency_key': self.context.idempotency_key,
            'timestamp': self.context.timestamp.isoformat(),
            'metadata': {
                'source_service': self.context.source_service,
                'version': self.context.version,
                **(self.context.metadata or {})
            },
            'payload': self.data if isinstance(self.data, dict) else {}
        }


class EventContextManager:
    """
    Manages event context throughout processing lifecycle.
    
    This can be used by any service that processes events.
    """
    
    def __init__(self, logger=None):
        self.logger = logger
    
    def extract_context(self, event: Dict[str, Any]) -> EventContext:
        """Extract and validate event context"""
        context = EventContext.from_event(event)
        
        # Validate required fields
        if not context.event_id and self.logger:
            self.logger.warning("Event missing event_id", extra={'event': event})
        
        if not context.event_type:
            raise ValueError("Event missing required event_type")
        
        # Apply correlation context
        context.apply_correlation()
        
        # Log event reception
        if self.logger:
            self.logger.info(
                f"Processing {context.event_type} event",
                extra=context.to_dict()
            )
        
        return context
    
    def log_event_completion(
        self,
        context: EventContext,
        success: bool,
        duration_ms: float,
        error: Optional[Exception] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """Log event processing completion"""
        if not self.logger:
            return
            
        log_data = {
            **context.to_dict(),
            'success': success,
            'duration_ms': duration_ms,
            **(additional_data or {})
        }
        
        if success:
            self.logger.info(
                f"Completed processing {context.event_type}",
                extra=log_data
            )
        else:
            self.logger.error(
                f"Failed to process {context.event_type}: {error}",
                extra={
                    **log_data,
                    'error_type': type(error).__name__ if error else 'Unknown'
                },
                exc_info=error
            )


# Backwards compatibility imports
__all__ = [
    'EventContext',
    'EventPayload',
    'EventContextManager'
]