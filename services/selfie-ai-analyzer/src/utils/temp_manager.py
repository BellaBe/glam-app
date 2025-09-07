# services/selfie-ai-analyzer/src/utils/temp_manager.py
import asyncio
import shutil
from pathlib import Path
from shared.utils.logger import ServiceLogger

class TempManager:
    """Manage temporary file workspace"""
    
    def __init__(self, base_dir: str, logger: ServiceLogger):
        self.base_dir = Path(base_dir)
        self.logger = logger
    
    async def create_workspace(self, analysis_id: str) -> Path:
        """Create temporary workspace for analysis"""
        work_dir = self.base_dir / analysis_id
        work_dir.mkdir(parents=True, exist_ok=True)
        return work_dir
    
    async def schedule_cleanup(self, work_dir: Path, hours: int):
        """Schedule cleanup after specified hours"""
        await asyncio.sleep(hours * 3600)
        await self.cleanup_directory(work_dir)
    
    async def cleanup_directory(self, work_dir: Path):
        """Clean up a specific directory"""
        try:
            if work_dir.exists():
                shutil.rmtree(work_dir)
                self.logger.debug(f"Cleaned up {work_dir}")
        except Exception as e:
            self.logger.exception(f"Failed to cleanup {work_dir}: {e}")
    
    async def cleanup_all(self):
        """Clean up all temp directories"""
        try:
            if self.base_dir.exists():
                shutil.rmtree(self.base_dir)
                self.logger.info("Cleaned up all temp files")
        except Exception as e:
            self.logger.exception(f"Failed to cleanup temp directory: {e}")