# services/webhook-service/src/repositories/platform_config_repository.py
"""Repository for platform configuration operations."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shared.database.repository import Repository
from ..models.platform_config import PlatformConfiguration
from ..models.webhook_entry import WebhookSource


class PlatformConfigRepository(Repository[PlatformConfiguration]):
    """Repository for platform configuration operations"""
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(PlatformConfiguration, session_factory)
    
    async def get_by_source(
        self,
        source: WebhookSource
    ) -> Optional[PlatformConfiguration]:
        """Get configuration for a specific source"""
        async with self.session_factory() as session:
            stmt = select(PlatformConfiguration).where(
                PlatformConfiguration.source == source,
                PlatformConfiguration.active == True
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def create_or_update(
        self,
        source: WebhookSource,
        webhook_secret: str,
        api_version: Optional[str] = None,
        endpoints: Optional[dict] = None
    ) -> PlatformConfiguration:
        """Create or update platform configuration"""
        async with self.session_factory() as session:
            # Check if exists
            stmt = select(PlatformConfiguration).where(
                PlatformConfiguration.source == source
            )
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()
            
            if config:
                # Update existing
                config.webhook_secret = webhook_secret
                config.api_version = api_version
                config.endpoints = endpoints
                config.active = True
            else:
                # Create new
                config = PlatformConfiguration(
                    source=source,
                    webhook_secret=webhook_secret,
                    api_version=api_version,
                    endpoints=endpoints,
                    active=True
                )
                session.add(config)
            
            await session.commit()
            await session.refresh(config)
            
            return config