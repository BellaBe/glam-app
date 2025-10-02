# services/catalog-ai-analyzer/src/lifecycle.py
from typing import Optional, List
import asyncio
from shared.messaging.jetstream_client import JetStreamClient
from shared.utils.logger import ServiceLogger
from .config import ServiceConfig
from .services.catalog_ai_service import CatalogAIService
from .services.mediapipe_analyzer import MediaPipeAnalyzer
from .services.openai_analyzer import OpenAIAnalyzer
from .events.publishers import CatalogAIPublisher
from .events.listeners import CatalogAnalysisRequestedListener

class ServiceLifecycle:
    """Manages catalog AI analyzer service lifecycle"""
    
    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        
        # Connections
        self.messaging_client: Optional[JetStreamClient] = None
        
        # Components
        self.mediapipe_analyzer: Optional[MediaPipeAnalyzer] = None
        self.openai_analyzer: Optional[OpenAIAnalyzer] = None
        self.catalog_ai_service: Optional[CatalogAIService] = None
        self.event_publisher: Optional[CatalogAIPublisher] = None
        
        # Listeners
        self._listeners: List = []
    
    async def startup(self) -> None:
        """Initialize all components"""
        try:
            self.logger.info("Starting catalog AI analyzer service...")
            
            # 1. Messaging
            await self._init_messaging()
            
            # 2. Analyzers
            self._init_analyzers()
            
            # 3. Main service
            self._init_service()
            
            # 4. Event listeners
            await self._init_listeners()
            
            self.logger.info("Catalog AI analyzer service started successfully")
            
        except Exception as e:
            self.logger.critical("Service startup failed", exc_info=True)
            await self.shutdown()
            raise
    
    async def shutdown(self) -> None:
        """Graceful shutdown"""
        self.logger.info("Shutting down catalog AI analyzer service")
        
        # Stop listeners
        for listener in self._listeners:
            try:
                await listener.stop()
            except Exception:
                self.logger.exception("Listener stop failed", exc_info=True)
        
        # Close analyzers
        if self.openai_analyzer:
            await self.openai_analyzer.close()
        
        if self.catalog_ai_service:
            await self.catalog_ai_service.close()
        
        # Close messaging
        if self.messaging_client:
            try:
                await self.messaging_client.close()
            except Exception:
                self.logger.exception("Messaging close failed", exc_info=True)
        
        self.logger.info("Shutdown complete")
    
    async def _init_messaging(self) -> None:
        """Initialize NATS/JetStream"""
        self.messaging_client = JetStreamClient(self.logger)
        await self.messaging_client.connect([self.config.nats_url])
        await self.messaging_client.ensure_stream("GLAM_EVENTS", ["evt.*", "cmd.*"])
        
        # Initialize publisher
        self.event_publisher = CatalogAIPublisher(
            jetstream_client=self.messaging_client,
            logger=self.logger
        )
        
        self.logger.info("Messaging initialized")
    
    def _init_analyzers(self) -> None:
        """Initialize MediaPipe and OpenAI analyzers"""
        self.mediapipe_analyzer = MediaPipeAnalyzer(
            config=self.config,
            logger=self.logger
        )
        
        self.openai_analyzer = OpenAIAnalyzer(
            config=self.config,
            logger=self.logger
        )
        
        self.logger.info("Analyzers initialized")
    
    def _init_service(self) -> None:
        """Initialize main service"""
        self.catalog_ai_service = CatalogAIService(
            config=self.config,
            mediapipe=self.mediapipe_analyzer,
            openai=self.openai_analyzer,
            logger=self.logger
        )
        
        # Wrap service to publish events after each item
        original_analyze = self.catalog_ai_service.analyze_single_item
        
        async def wrapped_analyze(merchant_id, correlation_id, item):
            result = await original_analyze(merchant_id, correlation_id, item)
            
            # Publish analysis completed event
            await self.event_publisher.analysis_completed(
                payload=result,
                correlation_id=correlation_id
            )
            
            return result
        
        self.catalog_ai_service.analyze_single_item = wrapped_analyze
        
        self.logger.info("Catalog AI service initialized")
    
    async def _init_listeners(self) -> None:
        """Initialize event listeners"""
        listener = CatalogAnalysisRequestedListener(
            js_client=self.messaging_client,
            publisher=self.event_publisher,
            service=self.catalog_ai_service,
            logger=self.logger
        )
        
        await listener.start()
        self._listeners.append(listener)
        
        self.logger.info("Event listeners started")