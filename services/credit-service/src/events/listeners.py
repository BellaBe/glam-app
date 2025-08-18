# services/credit-service/src/events/listeners.py
from shared.api.correlation import set_correlation_context
from shared.messaging.listener import Listener
from shared.utils.exceptions import ValidationError

from ..schemas.events import (
    CreditsPurchasedPayload,
    MatchCompletedPayload,
    MerchantCreatedPayload,
    TrialStartedPayload,
)


class MerchantCreatedListener(Listener):
    """Listen for merchant creation"""

    @property
    def subject(self) -> str:
        return "evt.merchant.created.v1"

    @property
    def queue_group(self) -> str:
        return "credit-service-merchant-handler"

    @property
    def service_name(self) -> str:
        return "credit-service"

    def __init__(self, js_client, service, publisher, logger):
        super().__init__(js_client, logger)
        self.service = service
        self.publisher = publisher

    async def on_message(self, data: dict) -> None:
        """Process merchant created event"""
        # Set correlation context from event
        correlation_id = data.get("correlation_id", "unknown")
        set_correlation_context(correlation_id)

        try:
            payload = MerchantCreatedPayload(**data)
            await self.service.handle_merchant_created(payload, correlation_id)
            self.logger.info(f"Credit account created for merchant {payload.merchant_id}")
        except ValidationError as e:
            self.logger.error(f"Invalid merchant event: {e}")
            return  # ACK to drop invalid message
        except Exception as e:
            self.logger.error(f"Failed to create credit account: {e}")
            raise  # NACK for retry


class TrialStartedListener(Listener):
    """Listen for trial started events"""

    @property
    def subject(self) -> str:
        return "evt.billing.trial.started.v1"

    @property
    def queue_group(self) -> str:
        return "credit-service-trial-handler"

    @property
    def service_name(self) -> str:
        return "credit-service"

    def __init__(self, js_client, service, publisher, logger):
        super().__init__(js_client, logger)
        self.service = service
        self.publisher = publisher

    async def on_message(self, data: dict) -> None:
        """Process trial started event"""
        correlation_id = data.get("correlation_id", "unknown")
        set_correlation_context(correlation_id)

        try:
            payload = TrialStartedPayload(**data)
            result = await self.service.handle_trial_started(payload, correlation_id)

            # Publish granted event
            await self.publisher.credits_granted(result)

        except ValidationError as e:
            self.logger.error(f"Invalid trial event: {e}")
            return  # ACK
        except Exception as e:
            self.logger.error(f"Failed to grant trial credits: {e}")
            raise  # NACK


class CreditsPurchasedListener(Listener):
    """Listen for credit purchase events"""

    @property
    def subject(self) -> str:
        return "evt.billing.credits.purchased.v1"

    @property
    def queue_group(self) -> str:
        return "credit-service-purchase-handler"

    @property
    def service_name(self) -> str:
        return "credit-service"

    def __init__(self, js_client, service, publisher, logger):
        super().__init__(js_client, logger)
        self.service = service
        self.publisher = publisher

    async def on_message(self, data: dict) -> None:
        """Process credits purchased event"""
        correlation_id = data.get("correlation_id", "unknown")
        set_correlation_context(correlation_id)

        try:
            payload = CreditsPurchasedPayload(**data)
            result = await self.service.handle_credits_purchased(payload, correlation_id)

            # Publish granted event
            await self.publisher.credits_granted(result)

        except ValidationError as e:
            self.logger.error(f"Invalid purchase event: {e}")
            return  # ACK
        except Exception as e:
            self.logger.error(f"Failed to add purchased credits: {e}")
            raise  # NACK


class MatchCompletedListener(Listener):
    """Listen for AI match completion"""

    @property
    def subject(self) -> str:
        return "evt.ai.match.completed.v1"

    @property
    def queue_group(self) -> str:
        return "credit-service-match-handler"

    @property
    def service_name(self) -> str:
        return "credit-service"

    def __init__(self, js_client, service, publisher, logger):
        super().__init__(js_client, logger)
        self.service = service
        self.publisher = publisher

    async def on_message(self, data: dict) -> None:
        """Process match completed event"""
        correlation_id = data.get("correlation_id", "unknown")
        set_correlation_context(correlation_id)

        try:
            payload = MatchCompletedPayload(**data)
            result = await self.service.handle_match_completed(payload, correlation_id)

            # Publish appropriate events based on result
            if result.get("insufficient"):
                await self.publisher.credits_insufficient(result)
            else:
                await self.publisher.credits_consumed(result)

                if result.get("low_balance"):
                    await self.publisher.credits_low_balance(result)

                if result.get("exhausted"):
                    await self.publisher.credits_exhausted(result)

        except ValidationError as e:
            self.logger.error(f"Invalid match event: {e}")
            return  # ACK
        except Exception as e:
            self.logger.error(f"Failed to consume credit: {e}")
            raise  # NACK
