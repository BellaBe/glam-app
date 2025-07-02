from typing import Optional, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from shared.utils.logger import ServiceLogger
from ..repositories.preference_repository import PreferenceRepository
from ..models.entities import NotificationPreference
from ..schemas.requests import PreferenceUpdate
from ..exceptions import PreferencesNotFoundError
import secrets

class PreferenceService:
    """Notification preference management service"""
    
    def __init__(self, logger: ServiceLogger):
        self.logger = logger
    
    async def update_preferences(
        self,
        data: PreferenceUpdate,
        session: AsyncSession
    ) -> NotificationPreference:
        """Update or create notification preferences"""
        repo = PreferenceRepository(session)
        
        # Check if preferences exist
        preferences = await repo.get_by_shop_id(data.shop_id)
        
        if preferences:
            # Update existing
            preferences.email_enabled = data.email_enabled
            preferences.notification_types = data.notification_types
        else:
            # Create new
            preferences = await repo.create(
                shop_id=data.shop_id,
                shop_domain=data.shop_domain or "unknown.myshopify.com",
                email_enabled=data.email_enabled,
                notification_types=data.notification_types,
                unsubscribe_token=secrets.token_urlsafe(32)
            )
        
        await session.commit()
        return preferences
    
    async def get_preferences(
        self,
        shop_id: UUID,
        session: AsyncSession
    ) -> Optional[NotificationPreference]:
        """Get notification preferences for shop"""
        repo = PreferenceRepository(session)
        preferences = await repo.get_by_shop_id(shop_id)
        
        if not preferences:
            raise PreferencesNotFoundError(
                f"No preferences found for shop {shop_id}",
                user_id=str(shop_id)
            )
        
        return preferences
    
    async def get_preferences_by_token(
        self,
        token: str,
        session: AsyncSession
    ) -> Optional[NotificationPreference]:
        """Get preferences by unsubscribe token"""
        repo = PreferenceRepository(session)
        return await repo.get_by_token(token)
    
    async def unsubscribe_by_token(
        self,
        token: str,
        session: AsyncSession
    ) -> bool:
        """Unsubscribe using token"""
        repo = PreferenceRepository(session)
        
        preferences = await repo.get_by_token(token)
        if not preferences:
            raise PreferencesNotFoundError(
                "Invalid unsubscribe token",
                user_id="unknown"
            )
        
        preferences.email_enabled = False
        await session.commit()
        
        self.logger.info(f"Shop {preferences.shop_id} unsubscribed via token")
        return True
    
    async def toggle_notification_type(
        self,
        shop_id: UUID,
        notification_type: str,
        enabled: bool,
        session: AsyncSession
    ) -> NotificationPreference:
        """Toggle specific notification type"""
        repo = PreferenceRepository(session)
        
        preferences = await repo.get_by_shop_id(shop_id)
        if not preferences:
            raise PreferencesNotFoundError(
                f"No preferences found for shop {shop_id}",
                user_id=str(shop_id)
            )
        
        if preferences.notification_types is None:
            preferences.notification_types = {}
        
        preferences.notification_types[notification_type] = enabled
        await session.commit()
        
        return preferences