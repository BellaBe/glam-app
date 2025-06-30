from shared.messaging.subscriber import JetStreamEventSubscriber
from .types import EVENT_REGISTRY


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
        if self.event_type in EVENT_REGISTRY:
            return EVENT_REGISTRY[self.event_type].stream.value
        
        # For events not in registry, must override
        return self._stream_name_override()
    
    def _stream_name_override(self) -> str:
        """Override when subscribing to events not in registry"""
        raise NotImplementedError(
            f"Event {self.event_type} not in registry, "
            f"must override _stream_name_override"
        )