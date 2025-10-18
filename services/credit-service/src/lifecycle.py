import asyncio
from shared.messaging.jetstream_client import JetStreamClient
from shared.utils.logger import ServiceLogger
from .config import ServiceConfig
from .db.session import make_engine, make_session_factory
from .events.listeners import (
    BillingRecordCreatedListener,
    TrialActivatedListener,
    PurchaseCompletedListener,
    PurchaseRefundedListener,
    MatchCompletedListener
)
from .events.publishers import CreditEventPublisher
from .services.credit_service import CreditService


class ServiceLifecycle:
    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        self.messaging_client: JetStreamClient | None = None
        self.engine = None
        self.session_factory = None
        self.event_publisher: CreditEventPublisher | None = None
        self._listeners: list = []
        self.credit_service: CreditService | None = None
        self._tasks: list[asyncio.Task] = []

    async def startup(self) -> None:
        try:
            self.logger.info("Starting credit service components...")
            await self._init_messaging()
            await self._init_database()
            self._init_services()
            await self._init_listeners()
            self.logger.info(f"{self.config.service_name} started successfully")
        except Exception:
            self.logger.critical("Service failed to start", exc_info=True)
            await self.shutdown()
            raise

    async def shutdown(self) -> None:
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        for listener in self._listeners:
            try:
                await listener.stop()
            except Exception:
                self.logger.exception("Listener stop failed", exc_info=True)
        if self.messaging_client:
            try:
                await self.messaging_client.close()
            except Exception:
                self.logger.exception("Messaging close failed", exc_info=True)
        if self.engine:
            try:
                await self.engine.dispose()
            except Exception:
                self.logger.exception("Engine dispose failed", exc_info=True)

    async def _init_messaging(self) -> None:
        self.messaging_client = JetStreamClient(self.logger)
        await self.messaging_client.connect([self.config.nats_url])
        await self.messaging_client.ensure_stream("GLAM_EVENTS", ["evt.*", "cmd.*"])
        self.event_publisher = CreditEventPublisher(self.messaging_client, self.logger)

    async def _init_database(self) -> None:
        if not self.config.database_enabled:
            self.logger.info("Database disabled; skipping")
            return
        self.engine = make_engine(self.config.database_url)
        self.session_factory = make_session_factory(self.engine)

    def _init_services(self) -> None:
        if not self.session_factory or not self.event_publisher:
            raise RuntimeError("Session factory or publisher not ready")
        self.credit_service = CreditService(
            self.session_factory,
            self.event_publisher,
            self.logger,
            self.config.low_balance_threshold
        )

    async def _init_listeners(self) -> None:
        if not self.messaging_client or not self.credit_service:
            raise RuntimeError("Messaging or service not ready")
        
        listeners = [
            BillingRecordCreatedListener(self.messaging_client, self.credit_service, self.logger),
            TrialActivatedListener(self.messaging_client, self.credit_service, self.logger),
            PurchaseCompletedListener(self.messaging_client, self.credit_service, self.logger),
            PurchaseRefundedListener(self.messaging_client, self.credit_service, self.logger),
            MatchCompletedListener(self.messaging_client, self.credit_service, self.logger)
        ]
        
        for listener in listeners:
            await listener.start()
            self._listeners.append(listener)
