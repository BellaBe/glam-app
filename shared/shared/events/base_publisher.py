
from typing import Dict, Any, Optional

from .base import Streams
from .mappers import EVENT_REGISTRY, get_stream_subjects
from shared.messaging.publisher import JetStreamEventPublisher


class DomainEventPublisher(JetStreamEventPublisher):
    """
    Smart publisher that:
    1. Auto-configures streams based on domain
    2. Validates events belong to the correct stream
    3. Provides domain-specific helpers
    """
    
    # Concrete classes just set these two properties
    domain_stream: Optional[Streams] = None
    service_name_override: Optional[str] = None

    @property
    def stream_name(self) -> str:
        """Auto-determined from domain_stream"""
        if not self.domain_stream:
            raise NotImplementedError("domain_stream must be set")
        return self.domain_stream.value
    
    @property
    def subjects(self) -> list[str]:
        """Auto-determined from domain_stream"""
        if not self.domain_stream:
            raise NotImplementedError("domain_stream must be set")
        return get_stream_subjects(self.domain_stream)
    
    @property
    def service_name(self) -> str:
        """Uses override or defaults"""
        return self.service_name_override or "unknown-service"
    
    def _validate_event_type(self, event_type: str):
        """
        Ensures you can't accidentally publish a billing event 
        from the catalog service
        """
        if event_type in EVENT_REGISTRY:
            event_def = EVENT_REGISTRY[event_type]
            if event_def.stream != self.domain_stream:
                raise ValueError(
                    f"Event {event_type} belongs to {event_def.stream}, "
                    f"not {self.domain_stream}"
                )
        else:
            # For events not in registry, check prefix matches subjects
            if not any(event_type.startswith(subj.replace('*', '')) 
                      for subj in self.subjects):
                raise ValueError(
                    f"Event {event_type} doesn't match any subject pattern "
                    f"for stream {self.domain_stream}"
                )
    
    async def publish_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        subject: Optional[str] = None,
        correlation_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Override with same signature, adds validation"""
        self._validate_event_type(event_type)
        
        # Call parent with all parameters
        return await super().publish_event(
            event_type=event_type,
            payload=payload,
            subject=subject,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            metadata=metadata
        )
    
    async def publish_command(
        self, 
        command_type: str, 
        payload: Dict[str, Any], 
        **kwargs
    ) -> str:
        """Override to add validation"""
        # Ensure command format
        if not command_type.startswith('cmd.'):
            command_type = f'cmd.{command_type}'
        
        self._validate_event_type(command_type)
        
        return await super().publish_command(command_type, payload, **kwargs)
    
    async def publish_event_response(
        self, 
        event_type: str, 
        payload: Dict[str, Any], 
        **kwargs
    ) -> str:
        """Override to add validation"""
        # Ensure event format
        if not event_type.startswith('evt.'):
            event_type = f'evt.{event_type}'
        
        self._validate_event_type(event_type)
        
        return await super().publish_event_response(event_type, payload, **kwargs)
