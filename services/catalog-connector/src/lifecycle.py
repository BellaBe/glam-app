# src/lifecycle.py
import asyncio

from shared.database import DatabaseSessionManager, set_database_manager
from shared.messaging import JetStreamWrapper
from shared.utils.logger import create_logger

from .config import ConnectorServiceConfig
from .events.publishers import ConnectorEventPublisher
from .events.subscribers import SyncFetchRequestedSubscriber
from .repositories.bulk_operation_repository import BulkOperationRepository
from .repositories.fetch_operation_repository import FetchOperationRepository
from .services.bulk_operation_service import BulkOperationService
from .services.product_transformer import ProductTransformer


class ConnectorServiceLifecycle:
    """Manages connector service lifecycle and dependencies"""

    def __init__(self, config: ConnectorServiceConfig):
        self.config = config
        self.logger = create_logger(config.service_name)

        # External connections
        self.messaging_wrapper: JetStreamWrapper | None = None
        self.db_manager: DatabaseSessionManager | None = None

        # Repositories
        self.bulk_repo: BulkOperationRepository | None = None
        self.fetch_repo: FetchOperationRepository | None = None

        # Services
        self.transformer: ProductTransformer | None = None
        self.bulk_service: BulkOperationService | None = None

        # Event handling
        self.event_publisher: ConnectorEventPublisher | None = None

        # Background tasks
        self._tasks: list[asyncio.Task] = []

    async def startup(self) -> None:
        """Initialize all components in order"""
        self.logger.info(f"Starting {self.config.service_name}")

        # 1. Database
        if self.config.db_enabled:
            self.db_manager = DatabaseSessionManager(
                database_url=self.config.database_config.database_url, echo=self.config.debug
            )
            await self.db_manager.init()
            set_database_manager(self.db_manager)

        # 2. Messaging
        self.messaging_wrapper = JetStreamWrapper(self.logger)
        await self.messaging_wrapper.connect(self.config.nats_servers)

        # 3. Create publisher
        self.event_publisher = self.messaging_wrapper.create_publisher(ConnectorEventPublisher)

        # 4. Initialize repositories
        if self.db_manager:
            self.bulk_repo = BulkOperationRepository(self.db_manager.session_factory)
            self.fetch_repo = FetchOperationRepository(self.db_manager.session_factory)

        # 5. Initialize services
        self.transformer = ProductTransformer(self.logger)

        self.bulk_service = BulkOperationService(
            bulk_repo=self.bulk_repo,
            fetch_repo=self.fetch_repo,
            transformer=self.transformer,
            publisher=self.event_publisher,
            logger=self.logger,
            config=self.config,
        )

        # 6. Register dependencies for subscribers
        self.messaging_wrapper.register_dependency("bulk_service", self.bulk_service)
        self.messaging_wrapper.register_dependency("logger", self.logger)

        # 7. Start event subscribers
        await self.messaging_wrapper.start_subscriber(SyncFetchRequestedSubscriber)

        self.logger.info("Connector service startup completed")

    async def shutdown(self) -> None:
        """Graceful shutdown of all components"""
        self.logger.info(f"Shutting down {self.config.service_name}")

        # Cancel background tasks
        for task in self._tasks:
            task.cancel()

        # Close connections
        if self.messaging_wrapper:
            await self.messaging_wrapper.close()
        if self.db_manager:
            await self.db_manager.close()
