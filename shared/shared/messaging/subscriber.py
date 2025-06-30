# shared/events/subscriber.py

import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio

from nats.aio.client import Client
from nats.js import JetStreamContext
from nats.js.api import ConsumerConfig, DeliverPolicy, AckPolicy


class JetStreamEventSubscriber(ABC):
    """
    JetStream subscriber specifically for structured events.
    Combines base functionality with event handling in one class.
    """

    @property
    @abstractmethod
    def stream_name(self) -> str:
        """The JetStream stream name to subscribe to."""
        pass

    @property
    @abstractmethod
    def subject(self) -> str:
        """The subject pattern to subscribe to."""
        pass

    @property
    @abstractmethod
    def durable_name(self) -> str:
        """The durable consumer name."""
        pass

    @property
    @abstractmethod
    def event_type(self) -> str:
        """The expected event_type for validation."""
        pass

    def __init__(self, client: Client, js: JetStreamContext, logger: Optional[Any] = None):
        self.client = client
        self.js = js
        self._subscription = None
        self.logger = logger or self._get_default_logger()
    
    def _get_default_logger(self):
        """Get a default logger if none provided"""
        import logging
        return logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def on_event(self, event: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> None:
        """Process the validated event."""
        pass

    async def on_error(self, error: Exception, event: Dict[str, Any]) -> bool:
        """Handle processing errors. Return True to ack, False to retry."""
        self.logger.error(f"Error processing {self.event_type}: {error}")
        return False  # Default: retry

    async def listen(self) -> None:
        """Subscribe and process messages."""
        
        # Consumer config
        consumer_config = ConsumerConfig(
            durable_name=self.durable_name,
            deliver_policy=DeliverPolicy.ALL,
            ack_policy=AckPolicy.EXPLICIT,
            max_deliver=3,
            ack_wait=30,
            filter_subject=self.subject,
        )

        # Create or bind consumer
        try:
            await self.js.consumer_info(self.stream_name, self.durable_name)
            self.logger.info(f"Using existing consumer: {self.durable_name}")
        except:
            await self.js.add_consumer(self.stream_name, config=consumer_config)
            self.logger.info(f"Created new consumer: {self.durable_name}")

        # Subscribe
        self._subscription = await self.js.pull_subscribe(
            self.subject,
            durable=self.durable_name,
            stream=self.stream_name
        )

        self.logger.info(f"Listening on {self.stream_name}/{self.subject}")
        
        # Process messages
        while True:
            try:
                messages = await self._subscription.fetch(batch=10, timeout=1)
                for msg in messages:
                    await self._process_message(msg)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error fetching messages: {e}")
                await asyncio.sleep(1)

    async def _process_message(self, msg) -> None:
        """Process a single message with error handling."""
        try:
            # Parse message
            try:
                data = json.loads(msg.data.decode("utf-8"))
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON: {e}")
                await msg.ack()
                return

            # Validate structure
            required = ['event_id', 'event_type', 'timestamp', 'payload']
            if missing := [f for f in required if f not in data]:
                self.logger.error(f"Missing fields: {missing}")
                await msg.ack()
                return

            # Validate event type
            if self.event_type and data.get('event_type') != self.event_type:
                self.logger.warning(f"Wrong event type: expected {self.event_type}, got {data.get('event_type')}")
                await msg.ack()
                return

            # Extract headers
            headers = {}
            if msg.headers:
                headers = {k: v[0] if isinstance(v, list) else v for k, v in msg.headers.items()}

            # Process event
            try:
                await self.on_event(data, headers)
                await msg.ack()
            except Exception as e:
                should_ack = await self.on_error(e, data)
                if should_ack:
                    await msg.ack()
                    
        except Exception as e:
            self.logger.critical(f"Fatal error processing message: {e}", exc_info=True)
            try:
                await msg.ack()  # Prevent poison messages
            except:
                pass

    async def stop(self) -> None:
        """Stop listening."""
        if self._subscription:
            await self._subscription.unsubscribe()
            self._subscription = None