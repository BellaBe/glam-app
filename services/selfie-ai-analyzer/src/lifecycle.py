# services/selfie-ai-analyzer/src/lifecycle.py
import asyncio
from pathlib import Path
from .services.face_analyzer import FaceAnalyzer
from .services.color_extractor import ColorExtractor
from .services.season_calculator import SeasonCalculator
from .services.analysis_service import AnalysisService
from .utils.temp_manager import TempManager
from shared.utils.logger import ServiceLogger

class ServiceLifecycle:
    """Manages service components lifecycle"""
    
    def __init__(self, config, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        
        # Create worker queue for backpressure
        self.worker_queue = asyncio.Queue(maxsize=config.worker_queue_size)
        
        # Components
        self.face_analyzer = None
        self.color_extractor = None
        self.season_calculator = None
        self.temp_manager = None
        self.analysis_service = None
    
    async def startup(self) -> None:
        """Initialize all components"""
        try:
            self.logger.info("Starting Selfie AI Analyzer components...")
            
            # Initialize analyzers
            self.face_analyzer = FaceAnalyzer(self.config, self.logger)
            self.color_extractor = ColorExtractor(self.logger)
            self.season_calculator = SeasonCalculator(self.logger)
            self.temp_manager = TempManager(self.config.temp_dir, self.logger)
            
            # Initialize main service
            self.analysis_service = AnalysisService(
                face_analyzer=self.face_analyzer,
                color_extractor=self.color_extractor,
                season_calculator=self.season_calculator,
                temp_manager=self.temp_manager,
                config=self.config,
                logger=self.logger,
                queue=self.worker_queue
            )
            
            # Ensure temp directory exists
            Path(self.config.temp_dir).mkdir(parents=True, exist_ok=True)
            
            self.logger.info("Selfie AI Analyzer started successfully")
            
        except Exception as e:
            self.logger.critical("Service startup failed", exc_info=True)
            raise
    
    async def shutdown(self) -> None:
        """Graceful shutdown"""
        self.logger.info("Shutting down Selfie AI Analyzer")
        
        # Cleanup temp files
        if self.temp_manager:
            await self.temp_manager.cleanup_all()
        
        self.logger.info("Selfie AI Analyzer shutdown complete")