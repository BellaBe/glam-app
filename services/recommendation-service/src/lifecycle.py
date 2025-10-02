# services/recommendation-service/src/lifecycle.py
from typing import Optional
import asyncio
from prisma import Prisma
from shared.messaging.jetstream_client import JetStreamClient
from shared.utils.logger import ServiceLogger

from .config import ServiceConfig
from .repositories.match_repository import MatchRepository
from .services.recommendation_service import RecommendationService
from .services.season_compatibility_client import SeasonCompatibilityClient
from .events.publishers import RecommendationEventPublisher


class ServiceLifecycle:
    """Manages all service components lifecycle"""
    
    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        
        # Connections
        self.messaging_client: Optional[JetStreamClient] = None
        self.prisma: Optional[Prisma] = None
        self._db_connected = False
        
        # Components
        self.event_publisher: Optional[RecommendationEventPublisher] = None
        self.match_repo: Optional[MatchRepository] = None
        self.season_client: Optional[SeasonCompatibilityClient] = None
        self.recommendation_service: Optional[RecommendationService] = None
    
    async def startup(self) -> None:
        """Initialize all components in correct order"""
        try:
            self.logger.info("Starting Recommendation Service components...")
            
            # 1. Messaging (for events)
            await self._init_messaging()
            
            # 2. Database
            await self._init_database()
            
            # 3. Repositories
            self._init_repositories()
            
            # 4. External clients
            self._init_clients()
            
            # 5. Services
            self._init_services()
            
            self.logger.info(f"{self.config.service_name} started successfully")
            
        except Exception as e:
            self.logger.critical("Service startup failed", exc_info=True)
            await self.shutdown()
            raise
    
    async def shutdown(self) -> None:
        """Graceful shutdown in reverse order"""
        self.logger.info(f"Shutting down {self.config.service_name}")
        
        # Close messaging
        if self.messaging_client:
            try:
                await self.messaging_client.close()
            except Exception:
                self.logger.exception("Messaging close failed", exc_info=True)
        
        # Disconnect database
        if self.prisma and self._db_connected:
            try:
                await self.prisma.disconnect()
            except Exception:
                self.logger.exception("Prisma disconnect failed", exc_info=True)
        
        self.logger.info(f"{self.config.service_name} shutdown complete")
    
    async def _init_messaging(self) -> None:
        """Initialize NATS/JetStream for events"""
        self.messaging_client = JetStreamClient(self.logger)
        await self.messaging_client.connect([self.config.nats_url])
        await self.messaging_client.ensure_stream("GLAM_EVENTS", ["evt.*", "cmd.*"])
        
        # Initialize publisher
        self.event_publisher = RecommendationEventPublisher(
            jetstream_client=self.messaging_client,
            logger=self.logger
        )
        self.logger.info("Messaging client and publisher initialized")
    
    async def _init_database(self) -> None:
        """Initialize Prisma client"""
        if not self.config.database_enabled:
            self.logger.info("Database disabled; skipping Prisma initialization")
            return
        
        self.prisma = Prisma()
        try:
            await self.prisma.connect()
            self._db_connected = True
            self.logger.info("Prisma connected")
        except Exception as e:
            self.logger.exception(f"Prisma connect failed: {e}", exc_info=True)
            raise
    
    def _init_repositories(self) -> None:
        """Initialize repositories with Prisma client"""
        if not self._db_connected:
            self.logger.warning("Database not connected, skipping repositories")
            return
        
        self.match_repo = MatchRepository(self.prisma)
        self.logger.info("Match repository initialized")
    
    def _init_clients(self) -> None:
        """Initialize external service clients"""
        self.season_client = SeasonCompatibilityClient(
            base_url=self.config.season_compatibility_url,
            api_key=self.config.season_compatibility_api_key,
            timeout=self.config.season_compatibility_timeout,
            logger=self.logger
        )
        self.logger.info("Season Compatibility client initialized")
    
    def _init_services(self) -> None:
        """Initialize business services"""
        if not self.match_repo:
            raise RuntimeError("Match repository not initialized")
        if not self.season_client:
            raise RuntimeError("Season Compatibility client not initialized")
        
        self.recommendation_service = RecommendationService(
            repository=self.match_repo,
            season_client=self.season_client,
            min_score=self.config.min_score,
            logger=self.logger
        )
        self.logger.info("Recommendation service initialized")