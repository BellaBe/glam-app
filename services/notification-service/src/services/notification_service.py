# services/notification-service/src/services/notification_service.py
"""Core notification service with proper delegation to other services"""

from typing import Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
import asyncio

from ..repositories.notification_repository import NotificationRepository

from .email_service import EmailService
from .template_service import TemplateService
from .preference_service import PreferenceService
from .rate_limit_service import InMemoryRateLimitService
from ..events.publishers import NotificationEventPublisher
from ..providers.base import EmailMessage, EmailResult
from ..models.entities import Notification
from src.config import ServiceConfig
from shared.utils.logger import ServiceLogger
from src.exceptions import (
    TemplateNotFoundError,
    RateLimitExceededError,
    UnsubscribedError
)


class NotificationService:
    """Core notification business logic"""
    
    def __init__(
        self,
        config: ServiceConfig,
        publisher: NotificationEventPublisher,
        email_service: EmailService,
        template_service: TemplateService,
        preference_service: PreferenceService,
        rate_limit_service: InMemoryRateLimitService,
        notification_repository: NotificationRepository,
        logger: ServiceLogger
    ):
        self.config = config
        self.publisher = publisher
        self.email_service = email_service
        self.template_service = template_service
        self.preference_service = preference_service
        self.rate_limit_service = rate_limit_service
        self.notification_repo = notification_repository
        self.logger = logger
        
        # Bulk sending configuration
        self.bulk_config = {
            "default_batch_size": 100,
            "max_batch_size": 1000,
            "min_batch_size": 1,
            "batch_delay_seconds": 1.0,
            "max_delay_seconds": 60.0,
            "concurrent_batches": 10
        }
    
    async def send_notification(
        self,
        shop_id: UUID,
        shop_domain: str,
        recipient_email: str,
        notification_type: str,
        dynamic_content: Optional[Dict] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> UUID:
        """
        Send a single notification
        
        This is the main entry point for sending notifications. It orchestrates
        the entire process including preference checks, rate limiting, template
        rendering, and email delivery.
        """
        
        # Initialize dynamic content if not provided
        dynamic_content = dynamic_content or {}
        metadata = metadata or {}
        
        # Add shop information to dynamic content for templates
        dynamic_content.update({
            "shop_id": str(shop_id),
            "shop_domain": shop_domain,
            "shop_name": shop_domain.replace('.myshopify.com', '')
        })
        
        # 1. Check preferences
        self.logger.info(
            f"Checking preferences for {notification_type} to {recipient_email}",
            extra={
                "shop_id": str(shop_id),
                "notification_type": notification_type,
                "correlation_id": correlation_id
            }
        )
        
        can_send = await self.preference_service.can_send_notification(
            shop_id=shop_id,
            shop_domain=shop_domain,
            notification_type=notification_type
        )
        
        if not can_send:
            self.logger.info(
                f"Skipping {notification_type} for {shop_id} - disabled in preferences",
                extra={
                    "shop_id": str(shop_id),
                    "notification_type": notification_type,
                    "correlation_id": correlation_id
                }
            )
            raise UnsubscribedError(
                f"Notifications disabled for {notification_type}",
                user_id=str(shop_id),
                notification_type=notification_type
            )
        
        # 2. Check rate limits
        self.logger.info(
            f"Checking rate limits for {recipient_email}",
            extra={
                "recipient_email": recipient_email,
                "notification_type": notification_type,
                "correlation_id": correlation_id
            }
        )
        
        is_allowed = await self.rate_limit_service.check_and_increment(
            recipient=recipient_email,
            notification_type=notification_type
        )
        
        if not is_allowed:
            self.logger.warning(
                f"Rate limit exceeded for {recipient_email}",
                extra={
                    "recipient_email": recipient_email,
                    "notification_type": notification_type,
                    "correlation_id": correlation_id
                }
            )
            raise RateLimitExceededError(
                f"Rate limit exceeded for {recipient_email}",
                recipient_email=recipient_email,
                notification_type=notification_type
            )
        
        # 3. Get template
        self.logger.info(
            f"Fetching template for {notification_type}",
            extra={
                "notification_type": notification_type,
                "correlation_id": correlation_id
            }
        )
        
        template = await self.template_service.get_template_for_type(notification_type)
        if not template:
            raise TemplateNotFoundError(
                f"No template found for notification type: {notification_type}",
                notification_type=notification_type
            )
        
        # 4. Get unsubscribe token
        unsubscribe_token = await self.preference_service.get_unsubscribe_token(shop_id)
        
        # 5. Render template using template service
        self.logger.info(
            f"Rendering template for {notification_type}",
            extra={
                "template_id": str(template.id),
                "template_name": template.name,
                "correlation_id": correlation_id
            }
        )
        
        subject, html_body, text_body = await self.template_service.render_template(
            template=template,
            dynamic_content=dynamic_content,
            unsubscribe_token=unsubscribe_token
        )
        
        notification_create = Notification(
            shop_id=shop_id,
            shop_domain=shop_domain,
            recipient_email=recipient_email,
            notification_type=notification_type,
            template_id=template.id,
            subject=subject,
            content=html_body,
            status="pending",
            metadata={
                **metadata,
                "correlation_id": correlation_id,
                "template_name": template.name
            }
        )
        
        # 6. Create notification record
        notification = await self.notification_repo.create(notification_create)
        
        self.logger.info(
            f"Created notification record {notification.id}",
            extra={
                "notification_id": str(notification.id),
                "notification_type": notification_type,
                "correlation_id": correlation_id
            }
        )
        
        # 7. Send email
        try:
            email_message = EmailMessage(
                to_email=recipient_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                metadata={
                    "notification_id": str(notification.id),
                    "shop_id": str(shop_id),
                    "notification_type": notification_type,
                    "correlation_id": correlation_id
                }
            )
            provider_response: EmailResult = await self.email_service.send_email(message=email_message)
            
            
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
                    "correlation_id": correlation_id
                }
            )
            
            # Publish success event
            await self.publisher.publish_email_sent(
                notification_id=UUID(str(notification.id)),
                shop_id=shop_id,
                notification_type=notification_type,
                provider=provider_response.provider,
                provider_message_id=provider_response.provider_message_id if provider_response.provider_message_id else "No response received",
                correlation_id=correlation_id
            )
            
        except Exception as e:
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
                    "correlation_id": correlation_id
                }
            )
            
            # Publish failure event
            await self.publisher.publish_email_failed(
                notification_id=UUID(str(notification.id)),
                shop_id=shop_id,
                notification_type=notification_type,
                error=str(e),
                error_code=getattr(e, 'code', 'UNKNOWN_ERROR'),
                retry_count=1,
                will_retry=self._should_retry(e),
                correlation_id=correlation_id
            )
            
            raise
        
        return UUID(str(notification.id))
    
    async def send_bulk_notifications(
        self,
        notification_type: str,
        recipients: List[Dict],
        correlation_id: Optional[str] = None
    ) -> Dict:
        """
        Send bulk notifications efficiently
        
        Recipients should be a list of dicts with:
        - shop_id: UUID
        - shop_domain: str
        - email: str
        - dynamic_content: Dict (optional)
        """
        
        bulk_job_id = uuid4()
        start_time = datetime.now(timezone.utc)
        
        self.logger.info(
            f"Starting bulk notification job {bulk_job_id}",
            extra={
                "bulk_job_id": str(bulk_job_id),
                "notification_type": notification_type,
                "recipient_count": len(recipients),
                "correlation_id": correlation_id
            }
        )
        
        # Get template once for all recipients
        template = await self.template_service.get_template_for_type(notification_type)
        if not template:
            raise TemplateNotFoundError(
                f"No template found for notification type: {notification_type}",
                notification_type=notification_type
            )
        
        # Process with flow control using semaphore
        semaphore = asyncio.Semaphore(self.bulk_config["concurrent_batches"])
        
        async def send_with_control(recipient: Dict, index: int):
            """Send single email with concurrency control"""
            async with semaphore:
                try:
                    # Add delay between sends to prevent overwhelming
                    if index > 0:
                        delay = min(
                            self.bulk_config["batch_delay_seconds"] * (index // self.bulk_config["default_batch_size"]),
                            self.bulk_config["max_delay_seconds"]
                        )
                        await asyncio.sleep(delay)
                    
                    await self.send_notification(
                        shop_id=recipient["shop_id"],
                        shop_domain=recipient["shop_domain"],
                        recipient_email=recipient["email"],
                        notification_type=notification_type,
                        dynamic_content=recipient.get("dynamic_content", {}),
                        correlation_id=correlation_id,
                        metadata={
                            "bulk_job_id": str(bulk_job_id),
                            "batch_index": index
                        }
                    )
                    
                    return "sent"
                    
                except UnsubscribedError:
                    return "unsubscribed"
                except RateLimitExceededError:
                    return "rate_limited"
                except Exception as e:
                    self.logger.error(
                        f"Failed to send bulk email to {recipient['email']}: {e}",
                        extra={
                            "bulk_job_id": str(bulk_job_id),
                            "recipient_email": recipient["email"],
                            "error": str(e),
                            "correlation_id": correlation_id
                        }
                    )
                    return "failed"
        
        # Send all notifications concurrently with control
        tasks = [
            send_with_control(recipient, i) 
            for i, recipient in enumerate(recipients)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count results
        result_counts = {
            "sent": 0,
            "unsubscribed": 0,
            "rate_limited": 0,
            "failed": 0
        }
        
        for result in results:
            if isinstance(result, Exception):
                result_counts["failed"] += 1
            elif result in result_counts:
                result_counts[result] += 1
            else:
                result_counts["failed"] += 1
        
        # Calculate duration
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        # Log completion
        self.logger.info(
            f"Bulk notification job {bulk_job_id} completed",
            extra={
                "bulk_job_id": str(bulk_job_id),
                "duration_seconds": duration,
                "results": result_counts,
                "correlation_id": correlation_id
            }
        )
        
        # Publish completion event
        await self.publisher.publish_bulk_completed(
            bulk_job_id=bulk_job_id,
            notification_type=notification_type,
            total_recipients=len(recipients),
            total_sent=result_counts["sent"],
            total_failed=result_counts["failed"],
            total_skipped=result_counts["unsubscribed"] + result_counts["rate_limited"],
            duration_seconds=duration,
            correlation_id=correlation_id
        )
        
        return {
            "bulk_job_id": str(bulk_job_id),
            "notification_type": notification_type,
            "total_recipients": len(recipients),
            "total_sent": result_counts["sent"],
            "total_failed": result_counts["failed"],
            "total_unsubscribed": result_counts["unsubscribed"],
            "total_rate_limited": result_counts["rate_limited"],
            "duration_seconds": duration,
            "average_time_per_email": duration / len(recipients) if recipients else 0
        }
    
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
            shop_id=UUID(str(notification.shop_id)),
            shop_domain=notification.shop_domain,
            recipient_email=notification.recipient_email,
            notification_type=notification.type,
            dynamic_content=notification.extra_metadata.get("dynamic_content", {}),
            correlation_id=correlation_id,
            metadata={
                "retry_of": str(notification_id),
                "retry_attempt": notification.retry_count + 1
            }
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