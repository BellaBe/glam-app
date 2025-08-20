# services/credit-service/src/services/credit_service.py
from uuid import UUID

from shared.utils import generate_idempotency_key
from shared.utils.exceptions import NotFoundError
from shared.utils.logger import ServiceLogger

from ..repositories.credit_repository import CreditRepository
from ..schemas.credit import CreditBalanceOut, CreditTransactionOut
from ..schemas.events import (
    CreditsPurchasedPayload,
    MatchCompletedPayload,
    MerchantCreatedPayload,
    TrialStartedPayload,
)


class CreditService:
    """Credit business logic service"""

    def __init__(self, repository: CreditRepository, config, logger: ServiceLogger):
        self.repository = repository
        self.config = config
        self.logger = logger

    # Read operations (for API)

    async def get_balance(self, merchant_id: UUID, shop_domain: str, correlation_id: str) -> CreditBalanceOut:
        """Get credit balance with platform context"""

        # Find by merchant_id
        account = await self.repository.find_by_merchant_id(merchant_id)

        if not account:
            # Also try by domain for backwards compatibility
            account = await self.repository.find_by_shop_domain(shop_domain)

        if not account:
            raise NotFoundError(
                message="Credit account not found",
                resource="credit_account",
                resource_id=str(merchant_id),
            )

        # Verify domain matches
        if account.shop_domain != shop_domain:
            self.logger.warning(
                "Platform domain mismatch in credit lookup",
                extra={
                    "correlation_id": correlation_id,
                    "merchant_id": str(merchant_id),
                    "expected_domain": shop_domain,
                    "account_domain": account.shop_domain,
                },
            )

        return CreditBalanceOut(
            balance=account.balance,
            total_granted=account.total_granted,
            total_consumed=account.total_consumed,
            platform_name=account.platform_name,
            shop_domain=account.shop_domain,
        )

    async def get_transactions(
        self, merchant_id: UUID, page: int, limit: int, correlation_id: str
    ) -> tuple[int, list[CreditTransactionOut]]:
        """Get transaction history"""

        # Check account exists
        account = await self.repository.find_by_merchant_id(merchant_id)
        if not account:
            raise NotFoundError(
                message="Credit account not found",
                resource="credit_account",
                resource_id=str(merchant_id),
            )

        skip = (page - 1) * limit
        total, transactions = await self.repository.get_transactions(merchant_id, skip, limit)

        return total, [CreditTransactionOut.model_validate(tx) for tx in transactions]

    # Event handlers (write operations)

    async def handle_merchant_created(self, event: MerchantCreatedPayload, correlation_id: str) -> dict:
        """Create credit account for new merchant"""

        self.logger.info(
            "Creating credit account for new merchant",
            extra={
                "correlation_id": correlation_id,
                "merchant_id": str(event.merchant_id),
                "platform": event.platform,
                "shop_domain": event.shop_domain,
            },
        )

        account = await self.repository.create_account(
            merchant_id=event.merchant_id,
            platform_name=event.platform,
            platform_shop_id=event.shop_gid,
            shop_domain=event.shop_domain,
        )

        return {
            "merchant_id": event.merchant_id,
            "platform_name": account.platform_name,
            "balance": account.balance,
        }

    async def handle_trial_started(self, event: TrialStartedPayload, correlation_id: str) -> dict:
        """Grant trial credits"""

        self.logger.info(
            "Granting trial credits",
            extra={
                "correlation_id": correlation_id,
                "merchant_id": str(event.merchant_id),
                "credits": self.config.trial_credits,
            },
        )

        # Generate idempotency key
        reference_id = generate_idempotency_key("TRIAL", "GRANT", event.merchant_id)

        account, transaction = await self.repository.update_balance(
            merchant_id=event.merchant_id,
            amount=self.config.trial_credits,
            operation="credit",
            reference_type="trial",
            reference_id=reference_id,
            description="Trial credits granted",
        )

        return {
            "merchant_id": event.merchant_id,
            "amount": self.config.trial_credits,
            "balance": account.balance,
            "reference_type": "trial",
            "reference_id": reference_id,
            "platform_name": account.platform_name,
        }

    async def handle_credits_purchased(self, event: CreditsPurchasedPayload, correlation_id: str) -> dict:
        """Add purchased credits"""

        self.logger.info(
            "Adding purchased credits",
            extra={
                "correlation_id": correlation_id,
                "merchant_id": str(event.merchant_id),
                "credits": event.credits,
                "purchase_id": event.purchase_id,
            },
        )

        account, transaction = await self.repository.update_balance(
            merchant_id=event.merchant_id,
            amount=event.credits,
            operation="credit",
            reference_type="purchase",
            reference_id=event.purchase_id,
            description=f"Purchased {event.credits} credits",
        )

        return {
            "merchant_id": event.merchant_id,
            "amount": event.credits,
            "balance": account.balance,
            "reference_type": "purchase",
            "reference_id": event.purchase_id,
            "platform_name": account.platform_name,
        }

    async def handle_match_completed(self, event: MatchCompletedPayload, correlation_id: str) -> dict:
        """Consume credit for match"""

        self.logger.info(
            "Consuming credit for match",
            extra={
                "correlation_id": correlation_id,
                "merchant_id": str(event.merchant_id),
                "match_id": event.match_id,
            },
        )

        # Check balance before consuming
        account = await self.repository.find_by_merchant_id(event.merchant_id)
        if not account:
            self.logger.error(
                "No credit account for merchant",
                extra={
                    "correlation_id": correlation_id,
                    "merchant_id": str(event.merchant_id),
                },
            )
            raise NotFoundError(
                message="Credit account not found",
                resource="credit_account",
                resource_id=str(event.merchant_id),
            )

        if account.balance <= 0:
            # Insufficient credits
            return {
                "merchant_id": event.merchant_id,
                "insufficient": True,
                "attempted_amount": 1,
                "balance": 0,
                "platform_name": account.platform_name,
            }

        # Consume credit
        account, transaction = await self.repository.update_balance(
            merchant_id=event.merchant_id,
            amount=1,
            operation="debit",
            reference_type="match",
            reference_id=event.match_id,
            description=f"Match for shopper {event.shopper_id}",
            metadata={
                "shopper_id": event.shopper_id,
                "matched_items_count": event.matched_items_count,
            },
        )

        result = {
            "merchant_id": event.merchant_id,
            "amount": 1,
            "balance": account.balance,
            "reference_type": "match",
            "reference_id": event.match_id,
            "platform_name": account.platform_name,
        }

        # Check for low balance
        if account.balance < self.config.low_balance_threshold:
            result["low_balance"] = True
            result["threshold"] = self.config.low_balance_threshold

        # Check for exhausted
        if account.balance == 0:
            result["exhausted"] = True

        return result
