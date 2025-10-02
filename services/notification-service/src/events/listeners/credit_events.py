# services/notification-service/src/events/listeners/credit_events.py
from typing import Any

from shared.messaging import Listener, Subjects
from shared.messaging.events.base import EventEnvelope
from shared.utils.exceptions import ValidationError
from shared.utils.logger import ServiceLogger
from src.events.publishers import NotificationEventPublisher
from src.services.notification_service import NotificationService

from shared.messaging.events.credit import (
    CreditBalanceGrantedPayload,
    CreditBalanceExhaustedPayload,
    CreditBalanceLowPayload,
    CreditTrialGrantedPayload,
    CreditTrialLowPayload,
    CreditTrialExhaustedPayload,
)


class CreditEventsListener(Listener):
    """Handle all credit-related events"""

    @property
    def subject(self) -> str:
        return "evt.credit.>"

    @property
    def queue_group(self) -> str:
        return "notification-credit"

    @property
    def service_name(self) -> str:
        return "notification-service"

    def __init__(
        self,
        js_client,
        notification_service: NotificationService,
        event_publisher: NotificationEventPublisher,
        logger: ServiceLogger,
    ):
        super().__init__(js_client, logger)
        self.notification_service = notification_service
        self.event_publisher = event_publisher

    async def on_message(self, envelope: EventEnvelope) -> None:
        """Process credit events"""
        
        event_type = envelope.event_type
        
        try:
            
            if event_type == Subjects.CREDIT_TRIAL_GRANTED:
                await self._handle_trial_granted(envelope)
            elif event_type == Subjects.CREDIT_TRIAL_LOW:
                await self.handle_trial_low(envelope)
            elif event_type == Subjects.CREDIT_TRIAL_EXHAUSTED:
                await self._handle_trial_exhausted(envelope)
            elif event_type == Subjects.CREDIT_BALANCE_GRANTED:
                await self.handle_credit_granted(envelope)
            elif event_type == Subjects.CREDIT_BALANCE_LOW:
                await self._handle_credit_low(envelope)
            elif event_type == Subjects.CREDIT_BALANCE_EXHAUSTED:
                await self._handle_credit_exhausted(envelope)
            else:
                self.logger.debug(f"Unhandled credit event: {event_type}")
                return

        except ValidationError as e:
            self.logger.exception(f"Invalid {event_type} event: {e}")
        except Exception as e:
            self.logger.exception(f"Failed to process {event_type}: {e}")
            raise

    
    async def _handle_trial_granted(self, envelope: EventEnvelope): 
        """Trial credits granted - welcome email"""
        try:
            payload = CreditTrialGrantedPayload.model_validate(envelope.data)
        except ValidationError as e:
            self.logger.exception(
                "Invalid credit.trial_granted payload", extra={"event_id": envelope.event_id, "errors": e.errors()}
            )
            return
        try:
            notification = await self.notification_service.process_event(
                event_type=envelope.event_type,
                data=payload,
                event_id=f"{payload.identifiers.platform_name}_{envelope.source_service}_{envelope.event_id}",
                correlation_id=envelope.correlation_id,
            )
        except AttributeError:
            raise
        except Exception:
            raise
        self.logger.info(
            "Trial granted email sent",
            extra={
                "event_id": envelope.event_id,
                "merchant_id": str(payload.identifiers.merchant_id),
                "correlation_id": envelope.correlation_id,
            },
        )
        await self.event_publisher.email_sent(notification=notification, ctx=envelope)
    
    async def handle_trial_low(self, envelope: EventEnvelope):
        """Trial credits running low - prompt upgrade"""
        try:
            payload = CreditTrialLowPayload.model_validate(envelope.data)
        except ValidationError as e:
            self.logger.exception(
                "Invalid credit.trial_low payload", extra={"event_id": envelope.event_id, "errors": e.errors()}
            )
            return
        try:
            notification = await self.notification_service.process_event(
                event_type=envelope.event_type,
                data=payload,
                event_id=f"{payload.identifiers.platform_name}_{envelope.source_service}_{envelope.event_id}",
                correlation_id=envelope.correlation_id,
            )
        except AttributeError:
            raise
        except Exception:
            raise
        self.logger.info(
            "Trial low email sent",
            extra={
                "event_id": envelope.event_id,
                "merchant_id": str(payload.identifiers.merchant_id),
                "correlation_id": envelope.correlation_id,
            },
        )
        await self.event_publisher.email_sent(notification=notification, ctx=envelope)
    
    async def _handle_trial_exhausted(self, envelope: EventEnvelope):
        """ Trial credits exhausted - prompt upgrade """
        
        try:
            payload = CreditTrialExhaustedPayload.model_validate(envelope.data)
        except ValidationError as e:
            self.logger.exception(
                "Invalid credit.trial_exhausted payload", extra={"event_id": envelope.event_id, "errors": e.errors()}
            )
            return  # Don't retry bad data
        
        try:
        
            notification = await self.notification_service.process_event(
                event_type=envelope.event_type,
                data=payload,
                event_id=f"{payload.identifiers.platform_name}_{envelope.source_service}_{envelope.event_id}",
                correlation_id=envelope.correlation_id,
            )
        
        except AttributeError:
            raise
        except Exception:
            raise

        self.logger.info(
            "Trial exhausted email sent",
            extra={
                "event_id": envelope.event_id,
                "merchant_id": str(payload.identifiers.merchant_id),
                "correlation_id": envelope.correlation_id,
            },
        )

        await self.event_publisher.email_sent(notification=notification, ctx=envelope)
           
    async def handle_credit_granted(self, envelope: EventEnvelope):
        """Credits granted - confirmation email"""
        try:
            payload = CreditBalanceGrantedPayload.model_validate(envelope.data)
        except ValidationError as e:
            self.logger.exception(
                "Invalid credit.granted payload", extra={"event_id": envelope.event_id, "errors": e.errors()}
            )
            return
        try:
            notification = await self.notification_service.process_event(
                event_type=envelope.event_type,
                data=payload,
                event_id=f"{payload.identifiers.platform_name}_{envelope.source_service}_{envelope.event_id}",
                correlation_id=envelope.correlation_id,
            )
        except AttributeError:
            raise
        except Exception:
            raise
        self.logger.info(
            "Credit granted email sent",
            extra={
                "event_id": envelope.event_id,
                "merchant_id": str(payload.identifiers.merchant_id),
                "correlation_id": envelope.correlation_id,
            },
        )
        await self.event_publisher.email_sent(notification=notification, ctx=envelope)
                
    async def _handle_credit_low(self, envelope: EventEnvelope):
        """Credits running low - prompt top-up"""
        try:
            payload = CreditBalanceLowPayload.model_validate(envelope.data)
        except ValidationError as e:
            self.logger.exception(
                "Invalid credit.balance_low payload", extra={"event_id": envelope.event_id, "errors": e.errors()}
            )
            return
        try:
            notification = await self.notification_service.process_event(
                event_type=envelope.event_type,
                data=payload,
                event_id=f"{payload.identifiers.platform_name}_{envelope.source_service}_{envelope.event_id}",
                correlation_id=envelope.correlation_id,
            )
        except AttributeError:
            raise
        except Exception:
            raise
        self.logger.info(
            "Low credit balance email sent",
            extra={
                "event_id": envelope.event_id,
                "merchant_id": str(payload.identifiers.merchant_id),
                "correlation_id": envelope.correlation_id,
            },
        )
        await self.event_publisher.email_sent(notification=notification, ctx=envelope)
        
    async def _handle_credit_exhausted(self, envelope: EventEnvelope):
        """Credits fully exhausted - service interruption warning"""
        try:
            payload = CreditBalanceExhaustedPayload.model_validate(envelope.data)
        except ValidationError as e:
            self.logger.exception(
                "Invalid credit.balance_exhausted payload", extra={"event_id": envelope.event_id, "errors": e.errors()}
            )
            return
        try:
            notification = await self.notification_service.process_event(
                event_type=envelope.event_type,
                data=payload,
                event_id=f"{payload.identifiers.platform_name}_{envelope.source_service}_{envelope.event_id}",
                correlation_id=envelope.correlation_id,
            )
        except AttributeError:
            raise
        except Exception:
            raise
        self.logger.info(
            "Credit exhausted email sent",
            extra={
                "event_id": envelope.event_id,
                "merchant_id": str(payload.identifiers.merchant_id),
                "correlation_id": envelope.correlation_id,
            },
        )
        await self.event_publisher.email_sent(notification=notification, ctx=envelope)
        

    
    