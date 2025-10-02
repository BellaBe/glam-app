# services/token-service/src/lifecycle.py

from typing import Optional
from prisma import Prisma
from shared.utils.logger import ServiceLogger
from .config import ServiceConfig
from .repositories.token_repository import TokenRepository
from .services.token_service import TokenService
from .services.encryption_service import EncryptionService

class ServiceLifecycle:
    """Manages all service components lifecycle"""
    
    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        
        # Connections
        self.prisma: Optional[Prisma] = None
        self._db_connected = False
        
        # Components
        self.token_repo: Optional[TokenRepository] = None
        self.encryption_service: Optional[EncryptionService] = None
        self.token_service: Optional[TokenService] = None
    
    async def startup(self) -> None:
        """Initialize all components"""
        try:
            self.logger.info("Starting Token Service components...")
            
            # 1. Database
            await self._init_database()
            
            # 2. Encryption
            self._init_encryption()
            
            # 3. Repositories
            self._init_repositories()
            
            # 4. Services
            self._init_services()
            
            self.logger.info(f"{self.config.service_name} started successfully")
            
        except Exception as e:
            self.logger.critical("Service startup failed", exc_info=True)
            await self.shutdown()
            raise
    
    async def shutdown(self) -> None:
        """Graceful shutdown"""
        self.logger.info(f"Shutting down {self.config.service_name}")
        
        # Disconnect database
        if self.prisma and self._db_connected:
            try:
                await self.prisma.disconnect()
            except Exception:
                self.logger.exception("Prisma disconnect failed", exc_info=True)
        
        self.logger.info(f"{self.config.service_name} shutdown complete")
    
    async def _init_database(self) -> None:
        """Initialize Prisma client"""
        if not self.config.database_enabled:
            raise RuntimeError("Database is required for Token Service")
        
        self.prisma = Prisma()
        try:
            await self.prisma.connect()
            self._db_connected = True
            self.logger.info("Prisma connected")
        except Exception as e:
            self.logger.exception(f"Prisma connect failed: {e}", exc_info=True)
            raise
    
    def _init_encryption(self) -> None:
        """Initialize encryption service"""
        self.encryption_service = EncryptionService(
            encryption_key=self.config.encryption_key,
            key_id=self.config.encryption_key_id,
            logger=self.logger
        )
        self.logger.info("Encryption service initialized")
    
    def _init_repositories(self) -> None:
        """Initialize repositories"""
        if not self._db_connected:
            raise RuntimeError("Database not connected")
        
        self.token_repo = TokenRepository(self.prisma, self.logger)
        self.logger.info("Token repository initialized")
    
    def _init_services(self) -> None:
        """Initialize business services"""
        if not self.token_repo or not self.encryption_service:
            raise RuntimeError("Dependencies not initialized")
        
        self.token_service = TokenService(
            repository=self.token_repo,
            encryption=self.encryption_service,
            logger=self.logger
        )
        self.logger.info("Token service initialized")