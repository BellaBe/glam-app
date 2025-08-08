from shared.messaging.listener import Listener
from shared.messaging.jetstream_client import JetStreamClient
from shared.utils.logger import ServiceLogger
from shared.api.correlation import set_correlation_context
from ..services.credit_service import CreditService
from ..schemas.credit import CreditGrantEvent, TrialActivatedEvent, CreditGrantIn

class BillingCreditGrantListener(Listener):
    """Listen for billing credit grant events"""
    
    @property
    def subject(self) -> str:
        return "evt.billing.credits.grant.v1"
    
    @property
    def queue_group(self) -> str:
        return "credit-grant"
    
    @property
    def service_name(self) -> str:
        return "credit-service"
    
    def __init__(
        self,
        js_client: JetStreamClient,
        service: CreditService,
        logger: ServiceLogger
    ):
        super().__init__(js_client, logger)
        self.service = service
    
    async def on_message(self, data: dict) -> None:
        """Process credit grant event"""
        payload = CreditGrantEvent(**data)
        
        # Set correlation context
        set_correlation_context(payload.correlation_id)
        
        self.logger.info(
            f"Processing credit grant: {payload.shop_domain}",
            extra={
                "correlation_id": payload.correlation_id,
                "shop_domain": payload.shop_domain,
                "amount": payload.credits,
                "reason": payload.reason
            }
        )
        
        # Convert to internal DTO
        grant_dto = CreditGrantIn(
            shop_domain=payload.shop_domain,
            amount=payload.credits,
            reason=payload.reason,
            external_ref=payload.external_ref,
            metadata=payload.metadata
        )
        
        # Process grant
        from types import SimpleNamespace
        ctx = SimpleNamespace(correlation_id=payload.correlation_id)
        await self.service.grant_credits(grant_dto, ctx)


class BillingTrialActivatedListener(Listener):
    """Listen for trial activation events"""
    
    @property
    def subject(self) -> str:
        return "evt.billing.trial.activated.v1"
    
    @property
    def queue_group(self) -> str:
        return "credit-trial"
    
    @property
    def service_name(self) -> str:
        return "credit-service"
    
    def __init__(
        self,
        js_client: JetStreamClient,
        service: CreditService,
        logger: ServiceLogger
    ):
        super().__init__(js_client, logger)
        self.service = service
    
    async def on_message(self, data: dict) -> None:
        """Process trial activation event"""
        payload = TrialActivatedEvent(**data)
        
        # Only process if trial credits are specified
        if not payload.trial_credits:
            self.logger.info(
                f"Trial activated without credits: {payload.shop_domain}",
                extra={
                    "correlation_id": payload.correlation_id,
                    "shop_domain": payload.shop_domain
                }
            )
            return
        
        # Set correlation context
        set_correlation_context(payload.correlation_id)
        
        self.logger.info(
            f"Processing trial activation: {payload.shop_domain}",
            extra={
                "correlation_id": payload.correlation_id,
                "shop_domain": payload.shop_domain,
                "trial_credits": payload.trial_credits
            }
        )
        
        # Create grant DTO
        grant_dto = CreditGrantIn(
            shop_domain=payload.shop_domain,
            amount=payload.trial_credits,
            reason="trial",
            external_ref=f"trial-{payload.shop_domain}-{payload.ends_at.isoformat()}",
            metadata={
                "trial_days": payload.days,
                "ends_at": payload.ends_at.isoformat()
            }
        )
        
        # Process grant
        from types import SimpleNamespace
        ctx = SimpleNamespace(correlation_id=payload.correlation_id)
        await self.service.grant_credits(grant_dto, ctx)

