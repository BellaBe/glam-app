# shared/messaging/jetstream_wrapper.py
from typing import List, Optional, Dict, Type, Any, TypeVar, cast
import os
import asyncio

import nats
from nats.aio.client import Client
from nats.js import JetStreamContext

from shared.messaging.publisher import JetStreamEventPublisher
from shared.messaging.subscriber import JetStreamEventSubscriber
from .dependencies import ServiceDependencies, DepKeys

T = TypeVar('T', bound=JetStreamEventPublisher)

class JetStreamWrapper:
    """JetStream wrapper with service-scoped dependency injection"""
    
    def __init__(self, logger: Optional[Any] = None):
        self._client: Optional[Client] = None
        self._js: Optional[JetStreamContext] = None
        self._publishers: Dict[str, JetStreamEventPublisher] = {}
        self._subscribers: List[JetStreamEventSubscriber] = []
        self._tasks: List[asyncio.Task] = []
        self.logger = logger
        self.dependencies = ServiceDependencies()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Guaranteed cleanup even if caller forgets close()"""
        await self.close()
    
    @property
    def client(self) -> Client:
        """Get the NATS client (for backward compatibility)"""
        if not self._client:
            raise Exception("NATS client not connected")
        return self._client
    
    @property
    def js(self) -> JetStreamContext:
        """Get the JetStream context"""
        if not self._js:
            raise Exception("JetStream not initialized")
        return self._js
    
    @property
    def publishers(self) -> Dict[str, JetStreamEventPublisher]:
        """Get all registered publishers"""
        return self._publishers
    
    async def connect(self, servers: List[str]):
        """Connect to NATS and initialize JetStream"""
        try:
            # Connection options
            options = {
                "servers": servers,
                "max_reconnect_attempts": -1,
                "reconnect_time_wait": 2,
            }
            
            # Add authentication if provided
            if user := os.getenv("NATS_USER"):
                options["user"] = user
                options["password"] = os.getenv("NATS_PASSWORD", "")
            
            self._client = await nats.connect(**options)
            self._js = self._client.jetstream()
            
            if self.logger:
                self.logger.info(f"Connected to NATS with JetStream at {servers}")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to connect to NATS: {e}")
            raise
    
    async def close(self):
        """Enhanced cleanup with task cancellation"""
        # Cancel all subscriber tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for graceful shutdown
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Stop subscribers
        for subscriber in self._subscribers:
            try:
                await subscriber.stop()
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error stopping subscriber: {e}")
        
        # Close NATS connection
        if self._client and not self._client.is_closed:
            await self._client.close()
            if self.logger:
                self.logger.info("NATS connection closed")
    
    def is_connected(self) -> bool:
        """Health check helper for /healthz endpoints"""
        return bool(self._client and self._client.is_connected)
    
    def register_dependency(self, key: DepKeys, instance: Any) -> None:
        """
        Register a dependency for this wrapper's subscribers.
        Typical keys: see shared/messaging/dependencies.DepKeys.
        """
        self.dependencies.register(key, instance)
        if self.logger:
            self.logger.debug(f"Registered dependency: {key}")
    
    def create_publisher(self, publisher_class: Type[T]) -> T:
        """Create and cache a publisher instance"""
        class_name = publisher_class.__name__
        
        if class_name not in self._publishers:
            if not self._client or not self._js:
                raise Exception("Must connect to NATS before creating publishers")
            
            self._publishers[class_name] = publisher_class(self._client, self._js, self.logger)
            if self.logger:
                self.logger.info(f"Created publisher: {class_name}")
        
        return cast(T, self._publishers[class_name])
    
    def get_publisher(self, publisher_class: Type[T]) -> Optional[T]:
        """Get a publisher by class type"""
        publisher = self._publishers.get(publisher_class.__name__)
        return cast(T, publisher) if publisher else None
    
    def create_subscriber(self, subscriber_class: Type[JetStreamEventSubscriber]) -> JetStreamEventSubscriber:
        """Create subscriber with wrapper access for dependencies"""
        if not self._client or not self._js:
            raise Exception("Must connect to NATS before creating subscribers")
        
        # Pass wrapper reference so subscriber can access dependencies
        subscriber = subscriber_class(self._client, self._js, self.logger, self)
        self._subscribers.append(subscriber)
        if self.logger:
            self.logger.info(f"Created subscriber: {subscriber_class.__name__}")
        
        return subscriber
    
    async def start_subscriber(self, subscriber_class: Type[JetStreamEventSubscriber]):
        """Create and start a subscriber in the background"""
        subscriber = self.create_subscriber(subscriber_class)
        task = asyncio.create_task(subscriber.listen())
        self._tasks.append(task)  # Track for proper cleanup
        
        if self.logger:
            self.logger.info(f"Started subscriber: {subscriber_class.__name__}")
        
        return task