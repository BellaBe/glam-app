# File: services/notification-service/src/services/notification_service.py
"""Refactored notification service with improved separation of concerns"""

from typing import Optional

import time
from dataclasses import dataclass
from uuid import UUID

from shared.utils.logger import ServiceLogger

from .email_service import EmailService
from .template_service import TemplateService

from ..config import ServiceConfig
from ..repositories.notification_repository import NotificationRepository
from ..exceptions import TemplateNotFoundError
from ..events.publishers import NotificationEventPublisher
from ..providers.base import EmailMessage, EmailResult
from ..models.notification import Notification
from ..mappers.notification_mapper import NotificationMapper
from ..metrics import (
    increment_notification_sent,
    observe_notification_duration,
    observe_template_render_duration
)
from ..schemas import NotificationCreate


class NotificationService:
    """Core notification business logic"""
    
    def __init__(
        self,
        config: ServiceConfig,
        publisher: NotificationEventPublisher,
        email_service: EmailService,
        template_service: TemplateService,
        notification_mapper: NotificationMapper,
        notification_repository: NotificationRepository,
        logger: ServiceLogger
    ):
        self.config = config
        self.publisher = publisher
        self.email_service = email_service
        self.template_service = template_service
        self.notification_repo = notification_repository
        self.logger = logger
        self.mapper = notification_mapper
        
        # Bulk sending configuration
        self.bulk_config = {
            "default_batch_size": 100,
            "max_batch_size": 1000,
            "min_batch_size": 1,
            "batch_delay_seconds": 1.0,
            "max_delay_seconds": 60.0,
            "concurrent_batches": 10
        }
        
    async def create_and_send_notification(
        self,
        notification_create: NotificationCreate
    ) -> UUID:
        """
        Create and send a notification
        
        This method is the main entry point for creating and sending notifications.
        It handles preference checks, rate limiting, template rendering, and email delivery.
        Parameters:
            notification_create (NotificationCreate): The notification details
        """
        
        # Validate input
        if not notification_create.shop_id or not notification_create.shop_domain:
            raise ValueError("Shop ID and domain are required")
        
        # Create notification record
        notification = await self.create_notification(notification_create)
        
        # Send the notification
        return await self.send_notification(notification)
    
    
    async def create_notification(
        self,
        notification_create: NotificationCreate
    ) -> Notification:
        """
        Create and send a notification
        
        This method is a simplified entry point for sending notifications.
        It handles preference checks, rate limiting, template rendering, and email delivery.
        """
        
        # Extract notification details
        notification_type = notification_create.notification_type
        shop_id = notification_create.shop_id
        shop_domain = notification_create.shop_domain
        unsubscribe_token = notification_create.unsubscribe_token
        dynamic_content = notification_create.dynamic_content or {}
        extra_metadata = notification_create.extra_metadata or {}
        
        self.logger.info(
            "Creating and sending notification",
            extra={
                "shop_id": str(shop_id),
                "shop_domain": shop_domain,
                "notification_type": notification_type,
                "correlation_id": extra_metadata.get("correlation_id", None),
            }
        )
        
        template = await self.template_service.get_template_for_type(notification_type)
        
        self.logger.debug(
            f"Retrieved template for notification type {notification_type}",
            extra={
                "shop_id": str(shop_id),
                "shop_domain": shop_domain,
                "correlation_id": extra_metadata.get("correlation_id", None),
            }
        )
        if not template:
            self.logger.error(
                f"No template found for notification type: {notification_type}",
                extra={
                    "shop_id": str(shop_id),
                    "shop_domain": shop_domain,
                    "correlation_id": extra_metadata.get("correlation_id", None),
                }
            )
            raise TemplateNotFoundError(
                f"No template found for notification type: {notification_type}",
                notification_type=notification_type
            )
        
        template_start = time.time()
        
        subject, html_body, text_body = await self.template_service.render_template(
            template=template,
            dynamic_content=dynamic_content,
            unsubscribe_token=unsubscribe_token
        )
       
        observe_template_render_duration(
                template_type=notification_type,
                duration=time.time() - template_start
            )
        
        new_notification = self.mapper.create_to_model(
            notification_create,
            subject=subject,
            content=html_body
        )

        notification = await self.notification_repo.create(new_notification)

        self.logger.info(
            f"Created notification record {notification.id}",
            extra={
                "notification_id": str(notification.id),
                "notification_type": notification_type,
                "correlation_id": extra_metadata.get("correlation_id", None),
            }
        )
        
        return notification
        
    async def send_notification(
        self,
        notification: Notification
    ) -> UUID:
        """
        Send a single notification
        
        This is the main entry point for sending notifications. It orchestrates
        the entire process including preference checks, rate limiting, template
        rendering, and email delivery.
        """
        start_time = time.time()
        
        self.logger.info(
            "Sending notification",
            extra={
                "notification_id": str(notification.id),
                "shop_id": str(notification.shop_id),
                "shop_domain": notification.shop_domain,
                "recipient_email": notification.recipient_email,
                "notification_type": notification.type,
                "correlation_id": (notification.extra_metadata or {}).get("correlation_id", None)
            }
        )
        
        try:
            email_message = EmailMessage(
                to_email=notification.recipient_email,
                subject=notification.subject,
                html_body=notification.content,
                text_body=notification.content,
            )
            provider_response: EmailResult = await self.email_service.send_email(message=email_message)
            
            increment_notification_sent(
                notification_type=notification.type,
                provider="sendgrid",
                status="success"
            )
            # Update notification status to sent
            await self.notification_repo.mark_as_sent(
                notification_id=UUID(str(notification.id)),
                provider=provider_response.provider,
                provider_message_id=provider_response.provider_message_id if provider_response.provider_message_id else "No response received",
            )
            
            self.logger.info(
                f"Email sent successfully via {provider_response.provider}",
                extra={
                    "notification_id": str(notification.id),
                    "provider_message_id": provider_response.provider_message_id,
                    "correlation_id": (notification.extra_metadata or {}).get("correlation_id", None)
                }
            )
            
            # Publish success event
            await self.publisher.publish_email_sent(
                notification_id=UUID(str(notification.id)),
                shop_id=UUID(str(notification.shop_id)),
                notification_type=notification.type,
                provider=provider_response.provider,
                provider_message_id=provider_response.provider_message_id if provider_response.provider_message_id else "No response received",
                correlation_id=(notification.extra_metadata or {}).get("correlation_id", None)
            )
            
        except Exception as e:
            # Record failure
            increment_notification_sent(
                notification_type=notification.type,
                provider="sendgrid",
                status="failure"
            )
            # Update notification status to failed
            await self.notification_repo.mark_as_failed(
                notification_id=UUID(str(notification.id)),
                error_message=str(e),
                retry_count=1
            )
            
            self.logger.error(
                f"Failed to send email: {e}",
                extra={
                    "notification_id": UUID(str(notification.id)),
                    "error": str(e),
                    "correlation_id": (notification.extra_metadata or {}).get("correlation_id", None)
                }
            )
            
            # Publish failure event
            await self.publisher.publish_email_failed(
                notification_id=UUID(str(notification.id)),
                shop_id=UUID(str(notification.shop_id)),
                notification_type=notification.type,
                error=str(e),
                error_code=getattr(e, 'code', 'UNKNOWN_ERROR'),
                retry_count=1,
                will_retry=self._should_retry(e),
                correlation_id=(notification.extra_metadata or {}).get("correlation_id", None)
            )
            
            raise
        
        finally:
          # Record total duration
            observe_notification_duration(
                notification_type=notification.type,
                provider="sendgrid",
                duration=time.time() - start_time
            )  
        
        return UUID(str(notification.id))
     
    async def retry_notification(
        self,
        notification_id: UUID,
        correlation_id: Optional[str] = None
    ) -> UUID:
        """Retry a failed notification"""
        
        # Get original notification
        notification = await self.notification_repo.get_by_id(notification_id)
        if not notification:
            raise ValueError(f"Notification {notification_id} not found")
        
        if notification.status != "failed":
            raise ValueError(
                f"Can only retry failed notifications. Current status: {notification.status}"
            )
        
        # Extract original data and retry
        return await self.send_notification(
            notification=notification
        )
    
    def _should_retry(self, error: Exception) -> bool:
        """Determine if error is retryable"""
        
        # List of retryable error types
        retryable_errors = {
            "PROVIDER_TIMEOUT",
            "PROVIDER_RATE_LIMITED",
            "NETWORK_ERROR",
            "TEMPORARY_FAILURE"
        }
        
        error_code = getattr(error, 'code', None)
        return error_code in retryable_errors
    
    async def list_notifications(self, offset, limit, shop_id: Optional[UUID] = None, status: Optional[str] = None, notification_type: Optional[str] = None) -> tuple[list[Notification], int]:
        """
        List notifications with optional filters
        
        Parameters:
            offset (int): Pagination offset
            limit (int): Number of records to return
            shop_id (Optional[UUID]): Filter by shop ID
            status (Optional[str]): Filter by notification status
            notification_type (Optional[str]): Filter by notification type
            
        Returns:
            Dict[List[Notification], int]: Tuple of notifications and total count
        """
        
        
        self.logger.info(
            "Listing notifications",
            extra={
                "shop_id": str(shop_id) if shop_id else None,
                "status": status,
                "notification_type": notification_type,
                "offset": offset,
                "limit": limit
            }
        )
        
        notifications, total_count = await self.notification_repo.list(
            shop_id=shop_id,
            status=status,
            notification_type=notification_type,
            offset=offset,
            limit=limit
        )
        
        self.logger.info(
            f"Listed {len(notifications)} notifications",
            extra={
                "shop_id": str(shop_id) if shop_id else None,
                "status": status,
                "notification_type": notification_type,
                "offset": offset,
                "limit": limit,
                "total_count": total_count
            }
        )
        
        return notifications, total_count
    
    async def get_notification(self, notification_id: UUID) -> Notification:
        """
        Get a single notification by ID
        
        Parameters:
            notification_id (UUID): Notification ID
            
        Returns:
            Notification: The requested notification
        """
        
        self.logger.info(
            f"Fetching notification {notification_id}",
            extra={"notification_id": str(notification_id)}
        )
        
        notification = await self.notification_repo.get_by_id(notification_id)
        
        if not notification:
            self.logger.warning(
                f"Notification {notification_id} not found",
                extra={"notification_id": str(notification_id)}
            )
            raise ValueError(f"Notification {notification_id} not found")
        
        self.logger.info(
            f"Fetched notification {notification.id}",
            extra={"notification_id": str(notification.id)}
        )
        
        return notification
       
