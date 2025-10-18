from shared.messaging.jetstream_client import JetStreamClient
from shared.messaging.listener import Listener
from shared.utils.logger import ServiceLogger
from src.services.credit_service import CreditService
from src.schemas.credit import (
    BillingRecordCreatedPayload,
    TrialActivatedPayload,
    PurchaseCompletedPayload,
    PurchaseRefundedPayload,
    MatchCompletedPayload
)
from shared.utils.exceptions import ValidationError
from pydantic import ValidationError as PydanticValidationError


class BillingRecordCreatedListener(Listener):
    @property
    def subject(self) -> str:
        return "evt.billing.record.created.v1"

    @property
    def queue_group(self) -> str:
        return "credit-billing-record"

    @property
    def service_name(self) -> str:
        return "credit-service"

    def __init__(self, js_client: JetStreamClient, service: CreditService, logger: ServiceLogger):
        super().__init__(js_client, logger)
        self.service = service

    async def on_message(self, data: dict) -> None:
        try:
            payload = BillingRecordCreatedPayload(**data)
            correlation_id = data.get("correlation_id", "unknown")
            await self.service.create_account(payload, correlation_id)
        except PydanticValidationError as e:
            raise ValidationError(message=f"Invalid payload: {e}", field="payload")

    async def on_error(self, error: Exception, data: dict) -> bool:
        if isinstance(error, ValidationError):
            return True  # ACK invalid messages
        if self.delivery_count >= self.max_deliver:
            await self.publish_event(
                subject=f"dlq.{self.service_name}.{self.queue_group}.failed",
                payload={"original_data": data, "error": str(error)}
            )
            return True
        return False


class TrialActivatedListener(Listener):
    @property
    def subject(self) -> str:
        return "evt.billing.trial.activated.v1"

    @property
    def queue_group(self) -> str:
        return "credit-trial-activated"

    @property
    def service_name(self) -> str:
        return "credit-service"

    def __init__(self, js_client: JetStreamClient, service: CreditService, logger: ServiceLogger):
        super().__init__(js_client, logger)
        self.service = service

    async def on_message(self, data: dict) -> None:
        try:
            payload = TrialActivatedPayload(**data)
            correlation_id = data.get("correlation_id", "unknown")
            await self.service.grant_trial_credits(payload, correlation_id)
        except PydanticValidationError as e:
            raise ValidationError(message=f"Invalid payload: {e}", field="payload")

    async def on_error(self, error: Exception, data: dict) -> bool:
        if isinstance(error, ValidationError):
            return True
        if self.delivery_count >= self.max_deliver:
            await self.publish_event(
                subject=f"dlq.{self.service_name}.{self.queue_group}.failed",
                payload={"original_data": data, "error": str(error)}
            )
            return True
        return False


class PurchaseCompletedListener(Listener):
    @property
    def subject(self) -> str:
        return "evt.billing.purchase.completed.v1"

    @property
    def queue_group(self) -> str:
        return "credit-purchase-completed"

    @property
    def service_name(self) -> str:
        return "credit-service"

    def __init__(self, js_client: JetStreamClient, service: CreditService, logger: ServiceLogger):
        super().__init__(js_client, logger)
        self.service = service

    async def on_message(self, data: dict) -> None:
        try:
            payload = PurchaseCompletedPayload(**data)
            correlation_id = data.get("correlation_id", "unknown")
            await self.service.grant_purchased_credits(payload, correlation_id)
        except PydanticValidationError as e:
            raise ValidationError(message=f"Invalid payload: {e}", field="payload")

    async def on_error(self, error: Exception, data: dict) -> bool:
        if isinstance(error, ValidationError):
            return True
        if self.delivery_count >= self.max_deliver:
            await self.publish_event(
                subject=f"dlq.{self.service_name}.{self.queue_group}.failed",
                payload={"original_data": data, "error": str(error)}
            )
            return True
        return False


class PurchaseRefundedListener(Listener):
    @property
    def subject(self) -> str:
        return "evt.billing.purchase.refunded.v1"

    @property
    def queue_group(self) -> str:
        return "credit-purchase-refunded"

    @property
    def service_name(self) -> str:
        return "credit-service"

    def __init__(self, js_client: JetStreamClient, service: CreditService, logger: ServiceLogger):
        super().__init__(js_client, logger)
        self.service = service

    async def on_message(self, data: dict) -> None:
        try:
            payload = PurchaseRefundedPayload(**data)
            correlation_id = data.get("correlation_id", "unknown")
            await self.service.refund_purchased_credits(payload, correlation_id)
        except PydanticValidationError as e:
            raise ValidationError(message=f"Invalid payload: {e}", field="payload")

    async def on_error(self, error: Exception, data: dict) -> bool:
        if isinstance(error, ValidationError):
            return True
        if self.delivery_count >= self.max_deliver:
            await self.publish_event(
                subject=f"dlq.{self.service_name}.{self.queue_group}.failed",
                payload={"original_data": data, "error": str(error)}
            )
            return True
        return False


class MatchCompletedListener(Listener):
    @property
    def subject(self) -> str:
        return "evt.recommendation.match.completed.v1"

    @property
    def queue_group(self) -> str:
        return "credit-match-completed"

    @property
    def service_name(self) -> str:
        return "credit-service"

    def __init__(self, js_client: JetStreamClient, service: CreditService, logger: ServiceLogger):
        super().__init__(js_client, logger)
        self.service = service

    async def on_message(self, data: dict) -> None:
        try:
            payload = MatchCompletedPayload(**data)
            correlation_id = data.get("correlation_id", "unknown")
            await self.service.consume_credit(payload, correlation_id)
        except PydanticValidationError as e:
            raise ValidationError(message=f"Invalid payload: {e}", field="payload")

    async def on_error(self, error: Exception, data: dict) -> bool:
        if isinstance(error, ValidationError):
            return True
        if self.delivery_count >= self.max_deliver:
            await self.publish_event(
                subject=f"dlq.{self.service_name}.{self.queue_group}.failed",
                payload={"original_data": data, "error": str(error)}
            )
            return True
        return False