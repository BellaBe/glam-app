from __future__ import annotations
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.repositories.credit_repository import CreditRepository
from src.schemas.credit import CreditBalanceOut, BillingRecordCreatedPayload, TrialActivatedPayload, PurchaseCompletedPayload, PurchaseRefundedPayload, MatchCompletedPayload
from src.events.publishers import CreditEventPublisher
from src.exceptions import CreditAccountNotFoundError, InvalidCreditAmountError
from shared.utils.logger import ServiceLogger


class CreditService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        publisher: CreditEventPublisher,
        logger: ServiceLogger,
        low_balance_threshold: int = 100
    ):
        self.session_factory = session_factory
        self.publisher = publisher
        self.logger = logger
        self.low_balance_threshold = low_balance_threshold

    async def get_balance(self, merchant_id: UUID) -> CreditBalanceOut:
        """Get credit balance for merchant (read-only API)"""
        async with self.session_factory() as session:
            repo = CreditRepository(session)
            account = await repo.get_account(merchant_id)
            
            if not account:
                raise CreditAccountNotFoundError(str(merchant_id))
            
            return CreditBalanceOut(
                balance=account.balance,
                trial_credits=account.trial_credits,
                purchased_credits=account.purchased_credits,
                total_granted=account.total_granted,
                total_consumed=account.total_consumed,
                platform_name=account.platform_name,
                platform_domain=account.platform_domain
            )

    async def create_account(self, data: BillingRecordCreatedPayload, correlation_id: str) -> None:
        """Handle evt.billing.record.created - create credit account"""
        async with self.session_factory() as session:
            repo = CreditRepository(session)
            
            # Idempotency check
            existing = await repo.get_account(data.merchant_id)
            if existing:
                self.logger.info(
                    f"Account already exists for merchant {data.merchant_id}",
                    extra={"merchant_id": str(data.merchant_id), "correlation_id": correlation_id}
                )
                return
            
            # Create account
            await repo.create_account(
                merchant_id=data.merchant_id,
                platform_name=data.platform_name,
                platform_id=data.platform_id,
                platform_domain=data.platform_domain
            )
            await session.commit()
            
            self.logger.info(
                f"Credit account created for merchant {data.merchant_id}",
                extra={"merchant_id": str(data.merchant_id), "correlation_id": correlation_id}
            )

    async def grant_trial_credits(self, data: TrialActivatedPayload, correlation_id: str) -> None:
        """Handle evt.billing.trial.activated - grant trial credits"""
        async with self.session_factory() as session:
            repo = CreditRepository(session)
            
            account = await repo.get_account(data.merchant_id)
            if not account:
                self.logger.error(
                    f"No account found for merchant {data.merchant_id}",
                    extra={"merchant_id": str(data.merchant_id), "correlation_id": correlation_id}
                )
                return
            
            # Idempotency check
            reference_id = f"trial_{data.merchant_id}"
            if await repo.transaction_exists("billing_trial", reference_id):
                self.logger.info(
                    "Trial credits already granted",
                    extra={"merchant_id": str(data.merchant_id), "correlation_id": correlation_id}
                )
                return
            
            # Grant trial credits
            old_balance = account.balance
            old_trial = account.trial_credits
            
            account.trial_credits += data.grant_amount
            account.balance = account.trial_credits + account.purchased_credits
            account.total_granted += data.grant_amount
            
            # Record transaction
            await repo.create_transaction(
                account_id=account.id,
                merchant_id=account.merchant_id,
                amount=data.grant_amount,
                operation="credit",
                source="trial",
                balance_before=old_balance,
                balance_after=account.balance,
                trial_before=old_trial,
                trial_after=account.trial_credits,
                purchased_before=account.purchased_credits,
                purchased_after=account.purchased_credits,
                reference_type="billing_trial",
                reference_id=reference_id
            )
            
            await session.commit()
            
            # Emit event
            await self.publisher.credits_granted(
                merchant_id=account.merchant_id,
                amount=data.grant_amount,
                balance=account.balance,
                credit_type="trial",
                reference_type="billing_trial",
                reference_id=reference_id,
                platform_name=account.platform_name,
                correlation_id=correlation_id
            )

    async def grant_purchased_credits(self, data: PurchaseCompletedPayload, correlation_id: str) -> None:
        """Handle evt.billing.purchase.completed - grant purchased credits"""
        async with self.session_factory() as session:
            repo = CreditRepository(session)
            
            account = await repo.get_account(data.merchant_id)
            if not account:
                self.logger.error(
                    f"No account found for merchant {data.merchant_id}",
                    extra={"merchant_id": str(data.merchant_id), "correlation_id": correlation_id}
                )
                return
            
            # Extract credits from metadata
            credits = data.metadata.get("credits")
            if not credits or credits <= 0:
                self.logger.error(
                    f"Invalid or missing credits in purchase metadata: {data.payment_id}",
                    extra={"payment_id": data.payment_id, "correlation_id": correlation_id}
                )
                return
            
            # Idempotency check
            if await repo.transaction_exists("billing_payment", data.payment_id):
                self.logger.info(
                    f"Purchase {data.payment_id} already processed",
                    extra={"payment_id": data.payment_id, "correlation_id": correlation_id}
                )
                return
            
            # Grant purchased credits
            old_balance = account.balance
            old_purchased = account.purchased_credits
            
            account.purchased_credits += credits
            account.balance = account.trial_credits + account.purchased_credits
            account.total_granted += credits
            
            # Record transaction
            await repo.create_transaction(
                account_id=account.id,
                merchant_id=account.merchant_id,
                amount=credits,
                operation="credit",
                source="purchase",
                balance_before=old_balance,
                balance_after=account.balance,
                trial_before=account.trial_credits,
                trial_after=account.trial_credits,
                purchased_before=old_purchased,
                purchased_after=account.purchased_credits,
                reference_type="billing_payment",
                reference_id=data.payment_id,
                metadata={"product_id": data.product_id}
            )
            
            await session.commit()
            
            # Emit event
            await self.publisher.credits_granted(
                merchant_id=account.merchant_id,
                amount=credits,
                balance=account.balance,
                credit_type="purchased",
                reference_type="billing_payment",
                reference_id=data.payment_id,
                platform_name=account.platform_name,
                correlation_id=correlation_id
            )

    async def refund_purchased_credits(self, data: PurchaseRefundedPayload, correlation_id: str) -> None:
        """Handle evt.billing.purchase.refunded - deduct purchased credits"""
        async with self.session_factory() as session:
            repo = CreditRepository(session)
            
            account = await repo.get_account_for_update(data.merchant_id)
            if not account:
                self.logger.error(
                    f"No account found for merchant {data.merchant_id}",
                    extra={"merchant_id": str(data.merchant_id), "correlation_id": correlation_id}
                )
                return
            
            # Extract credits from metadata
            credits = data.metadata.get("credits")
            if not credits or credits <= 0:
                self.logger.error(
                    f"Invalid or missing credits in refund metadata: {data.payment_id}",
                    extra={"payment_id": data.payment_id, "correlation_id": correlation_id}
                )
                return
            
            # Idempotency check
            reference_id = f"refund_{data.payment_id}"
            if await repo.transaction_exists("refund", reference_id):
                self.logger.info(
                    f"Refund {data.payment_id} already processed",
                    extra={"payment_id": data.payment_id, "correlation_id": correlation_id}
                )
                return
            
            # Deduct from purchased only, bounded at 0
            old_balance = account.balance
            old_purchased = account.purchased_credits
            
            deduct_amount = min(credits, account.purchased_credits)
            account.purchased_credits = max(0, account.purchased_credits - deduct_amount)
            account.balance = account.trial_credits + account.purchased_credits
            
            # Record transaction
            await repo.create_transaction(
                account_id=account.id,
                merchant_id=account.merchant_id,
                amount=deduct_amount,
                operation="debit",
                source="refund",
                balance_before=old_balance,
                balance_after=account.balance,
                trial_before=account.trial_credits,
                trial_after=account.trial_credits,
                purchased_before=old_purchased,
                purchased_after=account.purchased_credits,
                reference_type="refund",
                reference_id=reference_id
            )
            
            await session.commit()
            
            # Emit event
            await self.publisher.credits_consumed(
                merchant_id=account.merchant_id,
                amount=deduct_amount,
                balance=account.balance,
                credit_type="purchased",
                reference_type="refund",
                reference_id=reference_id,
                platform_name=account.platform_name,
                correlation_id=correlation_id
            )

    async def consume_credit(self, data: MatchCompletedPayload, correlation_id: str) -> None:
        """Handle evt.recommendation.match.completed - consume 1 credit (trial first)"""
        async with self.session_factory() as session:
            repo = CreditRepository(session)
            
            # Row lock to prevent race conditions
            account = await repo.get_account_for_update(data.merchant_id)
            if not account:
                self.logger.error(
                    f"No account found for merchant {data.merchant_id}",
                    extra={"merchant_id": str(data.merchant_id), "correlation_id": correlation_id}
                )
                return
            
            # Check sufficient balance
            if account.balance <= 0:
                await self.publisher.insufficient(
                    merchant_id=account.merchant_id,
                    attempted_amount=1,
                    balance=0,
                    platform_name=account.platform_name,
                    correlation_id=correlation_id
                )
                self.logger.warning(
                    f"Insufficient credits for merchant {data.merchant_id}",
                    extra={"merchant_id": str(data.merchant_id), "balance": 0, "correlation_id": correlation_id}
                )
                return
            
            # Idempotency check
            if await repo.transaction_exists("match", data.match_id):
                self.logger.info(
                    f"Match {data.match_id} already processed",
                    extra={"match_id": data.match_id, "correlation_id": correlation_id}
                )
                return
            
            # Determine credit source (trial first)
            use_trial = account.trial_credits > 0
            old_trial = account.trial_credits
            old_purchased = account.purchased_credits
            old_balance = account.balance
            was_trial_exhausted_before = account.trial_exhausted
            
            if use_trial:
                account.trial_credits -= 1
                account.trial_credits_used += 1
            else:
                account.purchased_credits -= 1
            
            account.balance = account.trial_credits + account.purchased_credits
            account.total_consumed += 1
            
            # Record transaction
            await repo.create_transaction(
                account_id=account.id,
                merchant_id=account.merchant_id,
                amount=1,
                operation="debit",
                source="trial" if use_trial else "purchase",
                balance_before=old_balance,
                balance_after=account.balance,
                trial_before=old_trial,
                trial_after=account.trial_credits,
                purchased_before=old_purchased,
                purchased_after=account.purchased_credits,
                reference_type="match",
                reference_id=data.match_id,
                metadata={
                    "shopper_id": data.shopper_id,
                    "matched_items_count": data.matched_items_count
                }
            )
            
            await session.commit()
            
            # Emit consumption event
            await self.publisher.credits_consumed(
                merchant_id=account.merchant_id,
                amount=1,
                balance=account.balance,
                credit_type="trial" if use_trial else "purchase",
                reference_type="match",
                reference_id=data.match_id,
                platform_name=account.platform_name,
                correlation_id=correlation_id
            )
            
            # Handle trial-specific events
            if use_trial:
                await self.publisher.trial_consumed(
                    merchant_id=account.merchant_id,
                    trial_credits_used=account.trial_credits_used,
                    trial_credits_remaining=account.trial_credits,
                    correlation_id=correlation_id
                )
                
                # Check trial exhaustion (derived property)
                if account.trial_exhausted and not was_trial_exhausted_before:
                    await self.publisher.trial_exhausted(
                        merchant_id=account.merchant_id,
                        platform_name=account.platform_name,
                        correlation_id=correlation_id
                    )
            
            # Emit threshold events inline
            if 0 < account.balance < self.low_balance_threshold:
                await self.publisher.low_balance(
                    merchant_id=account.merchant_id,
                    balance=account.balance,
                    threshold=self.low_balance_threshold,
                    platform_name=account.platform_name,
                    correlation_id=correlation_id
                )
            elif account.balance == 0:
                await self.publisher.exhausted(
                    merchant_id=account.merchant_id,
                    platform_name=account.platform_name,
                    correlation_id=correlation_id
                )