from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import Repository
from ..models.entities import NotificationPreference

class PreferenceRepository:
    """Repository for preference operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.model = NotificationPreference
    
    async def create(self, **kwargs) -> NotificationPreference:
        """Create new preference"""
        preference = self.model(**kwargs)
        self.session.add(preference)
        await self.session.flush()
        return preference
    
    async def get_by_shop_id(self, shop_id: UUID) -> Optional[NotificationPreference]:
        """Get preferences by shop ID"""
        stmt = select(self.model).where(self.model.shop_id == shop_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_token(self, token: str) -> Optional[NotificationPreference]:
        """Get preferences by unsubscribe token"""
        stmt = select(self.model).where(self.model.unsubscribe_token == token)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_enabled_shops(self, notification_type: Optional[str] = None) -> List[UUID]:
        """Get list of shops with notifications enabled"""
        stmt = select(self.model.shop_id).where(self.model.email_enabled == True)
        
        if notification_type:
            # Filter by specific notification type enabled
            # This requires JSONB query
            from sqlalchemy import text
            stmt = stmt.where(
                text(f"notification_types->'{notification_type}' = 'true'")
            )
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def bulk_create_defaults(self, shop_ids: List[UUID]) -> List[NotificationPreference]:
        """Create default preferences for multiple shops"""
        preferences = []
        
        for shop_id in shop_ids:
            # Check if already exists
            existing = await self.get_by_shop_id(shop_id)
            if not existing:
                import secrets
                preference = self.model(
                    shop_id=shop_id,
                    shop_domain=f"shop_{shop_id}.myshopify.com",
                    email_enabled=True,
                    notification_types={},
                    unsubscribe_token=secrets.token_urlsafe(32)
                )
                self.session.add(preference)
                preferences.append(preference)
        
        if preferences:
            await self.session.flush()
        
        return preferences