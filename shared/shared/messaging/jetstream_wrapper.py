from typing import List, Optional, Dict, Type, Any
import os

import nats
from nats.aio.client import Client
from nats.js import JetStreamContext

from .publisher import JetStreamEventPublisher
from .subscriber import JetStreamEventSubscriber

class JetStreamWrapper:
    """
    JetStream wrapper that manages connection and provides easy access to publishers/subscribers.
    """
    
    def __init__(self, logger: Optional[Any] = None):
        self._client: Optional[Client] = None
        self._js: Optional[JetStreamContext] = None
        self._publishers: Dict[str, JetStreamEventPublisher] = {}
        self._subscribers: List[JetStreamEventSubscriber] = []
        self.logger = logger
    
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
    
    async def connect(self, servers: List[str]):
        """
        Connect to NATS and initialize JetStream.
        
        Args:
            servers: List of NATS server URLs
        """
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
        """Close the NATS connection and stop all subscribers"""
        # Stop all subscribers first
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
    
    def create_publisher(self, publisher_class: Type[JetStreamEventPublisher]) -> JetStreamEventPublisher:
        """
        Create and cache a publisher instance.
        
        Args:
            publisher_class: The publisher class to instantiate
            
        Returns:
            Publisher instance
        """
        class_name = publisher_class.__name__
        
        if class_name not in self._publishers:
            if not self._client or not self._js:
                raise Exception("Must connect to NATS before creating publishers")
            
            self._publishers[class_name] = publisher_class(self._client, self._js, self.logger)
            if self.logger:
                self.logger.info(f"Created publisher: {class_name}")
        
        return self._publishers[class_name]
    
    def create_subscriber(self, subscriber_class: Type[JetStreamEventSubscriber]) -> JetStreamEventSubscriber:
        """
        Create a subscriber instance.
        
        Args:
            subscriber_class: The subscriber class to instantiate
            
        Returns:
            Subscriber instance
        """
        if not self._client or not self._js:
            raise Exception("Must connect to NATS before creating subscribers")
        
        subscriber = subscriber_class(self._client, self._js, self.logger)
        self._subscribers.append(subscriber)
        if self.logger:
            self.logger.info(f"Created subscriber: {subscriber_class.__name__}")
        
        return subscriber
    
    async def start_subscriber(self, subscriber_class: Type[JetStreamEventSubscriber]):
        """
        Create and start a subscriber in the background.
        
        Args:
            subscriber_class: The subscriber class to instantiate and start
            
        Returns:
            The asyncio Task running the subscriber
        """
        import asyncio
        
        subscriber = self.create_subscriber(subscriber_class)
        task = asyncio.create_task(subscriber.listen())
        if self.logger:
            self.logger.info(f"Started subscriber: {subscriber_class.__name__}")
        
        return task