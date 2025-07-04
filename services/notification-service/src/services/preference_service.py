# services/notification-service/src/services/preference_service.py
"""Preference management service for notification settings"""

from typing import Dict, Optional, List
from uuid import UUID
from datetime import datetime, timezone
import secrets
from cachetools import TTLCache

from ..repositories.preference_repository import PreferenceRepository
from ..models.entities import NotificationPreference
from shared.utils.logger import ServiceLogger


class PreferenceService:
    """Service for managing notification preferences and unsubscribe tokens"""
    
    def __init__(
        self,
        preference_repository: PreferenceRepository,
        logger: ServiceLogger,
        cache_ttl: int = 300  # 5 minutes cache
    ):
        self.repo = preference_repository
        self.logger = logger
        
        # Cache for preferences (shop_id -> preferences)
        self._preference_cache = TTLCache(maxsize=1000, ttl=cache_ttl)
        
        # Default notification types and their default enabled state
        self.default_notification_types = {
            # System notifications (default enabled)
            "welcome": True,
            "registration_finish": True,
            "registration_sync": True,
            "billing_expired": True,
            "billing_changed": True,
            "billing_low_credits": True,
            "billing_zero_balance": True,
            "billing_deactivated": True,
            
            # Custom notifications (default disabled)
            "marketing": False,
            "announcement": False,
            "custom": False
        }
    
    async def can_send_notification(
        self,
        shop_id: UUID,
        shop_domain: str,
        notification_type: str
    ) -> bool:
        """
        Check if notification can be sent based on preferences
        
        Returns True if:
        1. No preferences exist (first time, use defaults)
        2. Email is globally enabled AND notification type is enabled
        """
        
        preferences = await self.get_or_create_preferences(shop_id, shop_domain)
        
        # Check global email enabled
        if not preferences.email_enabled:
            self.logger.info(
                f"Email globally disabled for shop {shop_id}",
                extra={
                    "shop_id": str(shop_id),
                    "shop_domain": shop_domain
                }
            )
            return False
        
        # Check specific notification type
        notification_enabled = preferences.notification_types.get(
            notification_type,
            self.default_notification_types.get(notification_type, True)
        )
        
        if not notification_enabled:
            self.logger.info(
                f"Notification type {notification_type} disabled for shop {shop_id}",
                extra={
                    "shop_id": str(shop_id),
                    "shop_domain": shop_domain,
                    "notification_type": notification_type
                }
            )
        
        return notification_enabled
    
    async def get_or_create_preferences(
        self,
        shop_id: UUID,
        shop_domain: str
    ) -> NotificationPreference:
        """Get preferences, creating with defaults if not exists"""
        
        # Check cache first
        cache_key = str(shop_id)
        if cache_key in self._preference_cache:
            return self._preference_cache[cache_key]
        
        # Get from repository
        preferences = await self.repo.get_by_shop_id(shop_id)
        
        if not preferences:
            # Create default preferences
            preferences = await self.repo.create(
                shop_id=shop_id,
                shop_domain=shop_domain,
                email_enabled=True,
                notification_types=self.default_notification_types.copy(),
                unsubscribe_token=self._generate_unsubscribe_token()
            )
            
            self.logger.info(
                f"Created default preferences for shop {shop_id}",
                extra={
                    "shop_id": str(shop_id),
                    "shop_domain": shop_domain
                }
            )
        
        # Cache the preferences
        self._preference_cache[cache_key] = preferences
        
        return preferences
    
    async def get_unsubscribe_token(self, shop_id: UUID) -> str:
        """Get unsubscribe token for shop"""
        
        preferences = await self.get_or_create_preferences(shop_id, shop_id)
        
        # Regenerate token if somehow missing
        if not preferences.unsubscribe_token:
            preferences.unsubscribe_token = self._generate_unsubscribe_token()
            await self.repo.update(
                shop_id=shop_id,
                unsubscribe_token=preferences.unsubscribe_token
            )
            
            # Clear cache to force reload
            cache_key = str(shop_id)
            if cache_key in self._preference_cache:
                del self._preference_cache[cache_key]
        
        return preferences.unsubscribe_token
    
    async def update_preferences(
        self,
        shop_id: UUID,
        email_enabled: Optional[bool] = None,
        notification_types: Optional[Dict[str, bool]] = None
    ) -> NotificationPreference:
        """Update notification preferences"""
        
        # Clear cache
        cache_key = str(shop_id)
        if cache_key in self._preference_cache:
            del self._preference_cache[cache_key]
        
        # Update preferences
        preferences = await self.repo.update(
            shop_id=shop_id,
            email_enabled=email_enabled,
            notification_types=notification_types
        )
        
        if not preferences:
            raise ValueError(f"Preferences not found for shop {shop_id}")
        
        self.logger.info(
            f"Updated preferences for shop {shop_id}",
            extra={
                "shop_id": str(shop_id),
                "email_enabled": email_enabled,
                "notification_types_updated": list(notification_types.keys()) if notification_types else []
            }
        )
        
        return preferences
    
    async def unsubscribe_by_token(
        self,
        unsubscribe_token: str,
        notification_type: Optional[str] = None
    ) -> NotificationPreference:
        """
        Handle unsubscribe by token
        
        If notification_type is provided, only unsubscribe from that type.
        Otherwise, disable all email notifications.
        """
        
        # Find preferences by token
        preferences = await self.repo.get_by_unsubscribe_token(unsubscribe_token)
        
        if not preferences:
            raise ValueError("Invalid unsubscribe token")
        
        # Clear cache
        cache_key = str(preferences.shop_id)
        if cache_key in self._preference_cache:
            del self._preference_cache[cache_key]
        
        if notification_type:
            # Unsubscribe from specific type
            notification_types = preferences.notification_types.copy()
            notification_types[notification_type] = False
            
            preferences = await self.repo.update(
                shop_id=preferences.shop_id,
                notification_types=notification_types
            )
            
            self.logger.info(
                f"Shop {preferences.shop_id} unsubscribed from {notification_type}",
                extra={
                    "shop_id": str(preferences.shop_id),
                    "notification_type": notification_type
                }
            )
        else:
            # Global unsubscribe
            preferences = await self.repo.update(
                shop_id=preferences.shop_id,
                email_enabled=False
            )
            
            self.logger.info(
                f"Shop {preferences.shop_id} globally unsubscribed",
                extra={"shop_id": str(preferences.shop_id)}
            )
        
        return preferences
    
    async def resubscribe(
        self,
        shop_id: UUID,
        notification_type: Optional[str] = None
    ) -> NotificationPreference:
        """
        Resubscribe to notifications
        
        If notification_type is provided, only resubscribe to that type.
        Otherwise, enable all email notifications.
        """
        
        # Clear cache
        cache_key = str(shop_id)
        if cache_key in self._preference_cache:
            del self._preference_cache[cache_key]
        
        if notification_type:
            # Get current preferences
            preferences = await self.get_or_create_preferences(shop_id, "")
            
            # Resubscribe to specific type
            notification_types = preferences.notification_types.copy()
            notification_types[notification_type] = True
            
            preferences = await self.repo.update(
                shop_id=shop_id,
                notification_types=notification_types
            )
            
            self.logger.info(
                f"Shop {shop_id} resubscribed to {notification_type}",
                extra={
                    "shop_id": str(shop_id),
                    "notification_type": notification_type
                }
            )
        else:
            # Global resubscribe with default notification types
            preferences = await self.repo.update(
                shop_id=shop_id,
                email_enabled=True,
                notification_types=self.default_notification_types.copy()
            )
            
            self.logger.info(
                f"Shop {shop_id} globally resubscribed",
                extra={"shop_id": str(shop_id)}
            )
        
        return preferences
    
    async def get_enabled_notification_types(
        self,
        shop_id: UUID
    ) -> List[str]:
        """Get list of enabled notification types for a shop"""
        
        preferences = await self.get_or_create_preferences(shop_id, "")
        
        if not preferences.email_enabled:
            return []
        
        # Merge with defaults for any missing types
        enabled_types = []
        all_types = {**self.default_notification_types, **preferences.notification_types}
        
        for notification_type, is_enabled in all_types.items():
            if is_enabled:
                enabled_types.append(notification_type)
        
        return enabled_types
    
    async def bulk_update_preferences(
        self,
        updates: List[Dict]
    ) -> int:
        """
        Bulk update preferences for multiple shops
        
        Each update should contain:
        - shop_id: UUID
        - email_enabled: Optional[bool]
        - notification_types: Optional[Dict[str, bool]]
        """
        
        updated_count = 0
        
        for update in updates:
            try:
                await self.update_preferences(
                    shop_id=update["shop_id"],
                    email_enabled=update.get("email_enabled"),
                    notification_types=update.get("notification_types")
                )
                updated_count += 1
            except Exception as e:
                self.logger.error(
                    f"Failed to update preferences for shop {update['shop_id']}: {e}",
                    extra={"shop_id": str(update["shop_id"]), "error": str(e)}
                )
        
        return updated_count
    
    def _generate_unsubscribe_token(self) -> str:
        """Generate secure unsubscribe token"""
        return secrets.token_urlsafe(32)
    
    async def clear_cache(self, shop_id: Optional[UUID] = None):
        """Clear preference cache"""
        if shop_id:
            cache_key = str(shop_id)
            if cache_key in self._preference_cache:
                del self._preference_cache[cache_key]
        else:
            self._preference_cache.clear()
        
        self.logger.info(
            "Preference cache cleared",
            extra={"shop_id": str(shop_id) if shop_id else "all"}
        )