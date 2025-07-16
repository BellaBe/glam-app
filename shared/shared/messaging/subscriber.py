# shared/messaging/subscriber.py
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TYPE_CHECKING
import asyncio

from nats.aio.client import Client
from nats.js import JetStreamContext
from nats.js.api import ConsumerConfig, DeliverPolicy, AckPolicy
from .dependencies import DepKeys

if TYPE_CHECKING:
    from .jetstream_wrapper import JetStreamWrapper

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

    def __init__(
        self, 
        client: Client, 
        js: JetStreamContext, 
        logger: Optional[Any] = None,
        wrapper: Optional['JetStreamWrapper'] = None
    ):
        """Constructor with optional wrapper for dependency access"""
        self.client = client
        self.js = js
        self.logger = logger or self._get_default_logger()
        self._subscription = None
        
        # Access to service dependencies via wrapper
        self._wrapper = wrapper
        
        # Debug initialization
        self.logger.debug(f"Initialized {self.__class__.__name__}")
        self.logger.debug(f"JetStream context: {self.js is not None}")
        self.logger.debug(f"NATS client connected: {self.client.is_connected if self.client else False}")

    def _get_default_logger(self):
        """Get a default logger if none provided"""
        import logging
        return logging.getLogger(self.__class__.__name__)
    
    def get_dependency(self, key: DepKeys) -> Any:
        """Get a service dependency with type-constrained keys"""
        if not self._wrapper:
            raise RuntimeError(
                f"Cannot access dependency '{key}' - wrapper not provided. "
                "This usually means the subscriber was created manually instead of via JetStreamWrapper."
            )
        return self._wrapper.dependencies.get(key)
    
    def dep(self, key: DepKeys) -> Any:
        """Shorter alias for get_dependency"""
        return self.get_dependency(key)

    @abstractmethod
    async def on_event(self, event: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> None:
        """Process the validated event - access dependencies via self.get_dependency()"""
        pass

    async def on_error(self, error: Exception, event: Dict[str, Any]) -> bool:
        """Handle processing errors with safety net for dependency access"""
        try:
            self.logger.error(f"Error processing {self.event_type}: {error}")
        except Exception as log_error:
            # Fallback if even logging fails - avoid print() in production
            try:
                import sys
                sys.stderr.write(f"Critical error in subscriber {self.__class__.__name__}: {error}\n")
                sys.stderr.write(f"Additionally, logging failed: {log_error}\n")
                sys.stderr.flush()
            except Exception:
                # Last resort - this should never happen but protects against closed stderr
                pass
        return False  # Default: retry

    async def listen(self) -> None:
        """Subscribe and process messages with exponential backoff on failures"""

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
        try:
            self._subscription = await self.js.pull_subscribe(
                self.subject, 
                durable=self.durable_name, 
                stream=self.stream_name
            )
            
            if self._subscription is None:
                raise Exception("Failed to create subscription")
                
            self.logger.info(f"Listening on {self.stream_name}/{self.subject}")
            
            error_count = 0
            max_errors = 5
            
            # Process messages with exponential backoff
            while True:
                try:
                    messages = await self._subscription.fetch(batch=10, timeout=1)
                    error_count = 0  # Reset on success
                    
                    for msg in messages:
                        await self._process_message(msg)
                        
                except asyncio.TimeoutError:
                    continue  # Normal - no messages
                except Exception as e:
                    error_count += 1
                    
                    if error_count > max_errors:
                        self.logger.error("Too many errors, stopping subscriber")
                        break
                    
                    # Exponential backoff with jitter
                    backoff = min(60, 2 ** error_count)
                    self.logger.warning(f"Error #{error_count}, backing off {backoff}s: {e}")
                    await asyncio.sleep(backoff)
                    
        except Exception as e:
            self.logger.error(f"Failed to create subscription: {e}")
            raise

    async def _process_message(self, msg) -> None:
        """Process a single message with error handling"""
        try:
            # Parse message
            try:
                data = json.loads(msg.data.decode("utf-8"))
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON: {e}")
                await msg.ack()
                return

            # Validate structure
            required = ["event_id", "event_type", "timestamp", "payload"]
            if missing := [f for f in required if f not in data]:
                self.logger.error(f"Missing fields: {missing}")
                await msg.ack()
                return

            # Validate event type
            if self.event_type and data.get("event_type") != self.event_type:
                self.logger.warning(
                    f"Wrong event type: expected {self.event_type}, got {data.get('event_type')}"
                )
                await msg.ack()
                return

            # Extract headers
            headers = {}
            if msg.headers:
                headers = {
                    k: v[0] if isinstance(v, list) else v
                    for k, v in msg.headers.items()
                }

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
        """Stop listening"""
        if self._subscription:
            try:
                await self._subscription.unsubscribe()
            except Exception as e:
                self.logger.error(f"Error unsubscribing: {e}")
            finally:
                self._subscription = None