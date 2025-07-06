# File: shared/shared/events/base_subscriber.py
from .mappers import get_stream_from_event_type
from shared.messaging.subscriber import JetStreamEventSubscriber


class DomainEventSubscriber(JetStreamEventSubscriber):
    """
    Smart subscriber that:
    1. Auto-determines stream from event type
    2. Provides helpers for cross-domain subscriptions
    3. Validates event structure
    """
    
    @property
    def stream_name(self) -> str:
        """Auto-determine stream from event type"""
        try:
            stream = get_stream_from_event_type(self.event_type)
            return stream.value
        except ValueError:
            # For events not following standard pattern, must override
            return self._stream_name_override()
    
    def _stream_name_override(self) -> str:
        """Override when subscribing to events not following standard pattern"""
        raise NotImplementedError(
            f"Event {self.event_type} doesn't follow standard pattern, "
            f"must override _stream_name_override"
        )