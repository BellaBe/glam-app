from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from shared.utils.logger import ServiceLogger
from shared.api.correlation import get_correlation_context

from ..repositories.notification_repository import NotificationRepository
from ..repositories.template_repository import TemplateRepository
from ..repositories.preference_repository import PreferenceRepository
from ..models.entities import Notification
from ..schemas.requests import NotificationCreate, BulkNotificationCreate
from ..providers.base import EmailMessage
from ..utils.template_engine import TemplateEngine
from ..utils.rate_limiter import RateLimiter
from ..exceptions import (
    NotificationNotFoundError,
    TemplateNotFoundError,
    TemplateRenderError,
    UnsubscribedError,
    RateLimitedError
)
from ..events.publishers import NotificationPublisher
from ..constants.notification_types import NotificationType
import secrets


class NotificationService:
    """Core notification business logic"""
    
    def __init__(
        self,
        publisher: NotificationPublisher,
        email_service,
        template_engine: TemplateEngine,
        rate_limiter: RateLimiter,
        logger: ServiceLogger
    ):
        self.publisher = publisher
        self.email_service = email_service
        self.template_engine = template_engine
        self.rate_limiter = rate_limiter
        self.logger = logger
    
    async def send_notification(
        self,
        data: NotificationCreate,
        session: AsyncSession
    ) -> Notification:
        """Send a single notification"""
        repo = NotificationRepository(Notification, session)
        template_repo = TemplateRepository(session)
        pref_repo = PreferenceRepository(session)
        
        # Check preferences
        preferences = await pref_repo.get_by_shop_id(data.shop_id)
        if preferences and not preferences.email_enabled:
            raise UnsubscribedError(
                user_id=str(data.shop_id),
                notification_type=data.notification_type,
                unsubscribed_at=preferences.updated_at.isoformat()
            )
        
        if preferences and data.notification_type in preferences.notification_types:
            if not preferences.notification_types[data.notification_type]:
                raise UnsubscribedError(
                    user_id=str(data.shop_id),
                    notification_type=data.notification_type
                )
        
        # Check rate limits
        can_send, reason = await self.rate_limiter.check_rate_limit(
            session, data.recipient_email, data.notification_type
        )
        if not can_send:
            raise RateLimitedError(
                message=reason or "Rate limit exceeded",
                limit=self.rate_limiter.burst_limit,
                window="1m"
            )
        
        # Get template
        template = None
        if data.template_id:
            template = await template_repo.get_by_id(data.template_id)
            if not template or not template.is_active:
                raise TemplateNotFoundError(
                    f"Template {data.template_id} not found or inactive",
                    template_name=str(data.template_id),
                    template_type=data.notification_type
                )
        else:
            # Get default template for type
            template = await template_repo.get_by_type_and_name(
                data.notification_type, f"{data.notification_type}_default"
            )
        
        if not template:
            raise TemplateNotFoundError(
                f"No template found for type {data.notification_type}",
                template_type=data.notification_type
            )
        
        # Prepare context
        context = {
            **data.dynamic_content,
            'unsubscribe_url': self._generate_unsubscribe_url(preferences.unsubscribe_token if preferences else None),
            'shop_name': data.shop_domain.replace('.myshopify.com', '')
        }
        
        # Render template
        try:
            subject = self.template_engine.render(template.subject_template, context)
            html_content = self.template_engine.render(template.body_template, context)
            text_content = self.template_engine.html_to_text(html_content)
        except Exception as e:
            raise TemplateRenderError(
                f"Failed to render template: {e}",
                template_name=template.name,
                render_error=str(e),
                missing_variables=self._get_missing_variables(e)
            )
        
        # Create notification record
        notification: Notification = await repo.create(
            shop_id=data.shop_id,
            shop_domain=data.shop_domain,
            recipient_email=data.recipient_email,
            type=data.notification_type,
            template_id=template.id,
            subject=subject,
            content=html_content,
            status="pending",
            extra_metadata={
                **data.metadata,
                "correlation_id": get_correlation_context()
            }
        )
        
        # Send email
        email_message = EmailMessage(
            to_email=data.recipient_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
        
        result = await self.email_service.send_email(email_message)
        
        # Update notification status
        if result.success:
            notification.status = "sent"
            notification.provider = self.email_service.current_provider
            notification.provider_message_id = result.provider_message_id
            notification.sent_at = datetime.utcnow()
            
            # Record send for rate limiting
            await self.rate_limiter.record_send(
                session, data.recipient_email, data.notification_type
            )
            
            # Publish success event
            correlation_id = get_correlation_context()
            await self.publisher.publish_email_sent(
                notification_id=UUID(str(notification.id)),
                shop_id=data.shop_id,
                notification_type=data.notification_type,
                provider_message_id=result.provider_message_id,
                correlation_id=correlation_id
                )
        else:
            notification.status = "failed"
            notification.error_message = result.error_message
            notification.retry_count += 1
            
            # Publish failure event
            await self.publisher.publish_email_failed(
                notification_id=UUID(str(notification.id)),
                shop_id=data.shop_id,
                notification_type=data.notification_type,
                error=result.error_message,
                error_code=result.error_code,
                retry_count=notification.retry_count,
                will_retry=self._should_retry(result.error_code, notification.retry_count),
                correlation_id=get_correlation_context()
            )
        
        await session.commit()
        return notification
    
    async def send_bulk_notifications(
        self,
        data: BulkNotificationCreate,
        session: AsyncSession
    ) -> List[Notification]:
        """Send bulk notifications"""
        notifications = []
        
        for recipient in data.recipients:
            try:
                notification_data = NotificationCreate(
                    shop_id=recipient['shop_id'],
                    shop_domain=recipient.get('shop_domain', 'unknown'),
                    recipient_email=recipient['email'],
                    notification_type=data.notification_type,
                    template_id=data.template_id,
                    dynamic_content=recipient.get('dynamic_content', {})
                )
                
                notification = await self.send_notification(notification_data, session)
                notifications.append(notification)
                
            except Exception as e:
                self.logger.error(
                    f"Failed to send bulk email to {recipient['email']}: {e}",
                    extra={"correlation_id": get_correlation_context()}
                )
        
        return notifications
    
    async def get_notification(
        self,
        notification_id: UUID,
        session: AsyncSession
    ) -> Optional[Notification]:
        """Get notification by ID"""
        repo = NotificationRepository(Notification, session)
        notification = await repo.get(notification_id)
        
        if not notification:
            raise NotificationNotFoundError(
                f"Notification {notification_id} not found",
                notification_id=str(notification_id)
            )
        
        return notification
    
    async def list_notifications(
        self,
        session: AsyncSession,
        shop_id: Optional[UUID] = None,
        status: Optional[str] = None,
        type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Notification]:
        """List notifications with filters"""
        repo = NotificationRepository(Notification, session)
        
        filters = {}
        if shop_id:
            filters['shop_id'] = shop_id
        if status:
            filters['status'] = status
        if type:
            filters['type'] = type
        
        return await repo.find(
            filters=filters,
            order_by=["-created_at"],
            skip=skip,
            limit=limit
        )
    
    async def count_notifications(
        self,
        session: AsyncSession,
        shop_id: Optional[UUID] = None,
        status: Optional[str] = None,
        type: Optional[str] = None
    ) -> int:
        """Count notifications"""
        repo = NotificationRepository(Notification, session)
        
        filters = {}
        if shop_id:
            filters['shop_id'] = shop_id
        if status:
            filters['status'] = status
        if type:
            filters['type'] = type
        
        return await repo.count(filters=filters)
    
    def _generate_unsubscribe_url(self, token: Optional[str]) -> str:
        """Generate unsubscribe URL"""
        if not token:
            token = secrets.token_urlsafe(32)
        return f"https://glamyouup.com/unsubscribe?token={token}"
    
    def _should_retry(self, error_code: str, retry_count: int) -> bool:
        """Determine if notification should be retried"""
        if retry_count >= 3:  # Max retries from config
            return False
        
        retryable_errors = [
            "PROVIDER_TIMEOUT",
            "PROVIDER_RATE_LIMITED",
            "NETWORK_ERROR"
        ]
        
        return error_code in retryable_errors
    
    def _get_missing_variables(self, exc: Exception) -> Optional[List[str]]:
        """Extract missing variables from template error"""
        # This would parse the Jinja2 error to find missing variables
        # For now, return None
        return None