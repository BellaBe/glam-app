# services/credit-service/src/repositories/credit_repository.py
from uuid import UUID

from prisma import Prisma
from prisma.errors import UniqueViolationError

from shared.utils.exceptions import NotFoundError


class CreditRepository:
    """Repository for credit operations using Prisma"""

    def __init__(self, prisma: Prisma):
        self.prisma = prisma

    async def create_account(
        self,
        merchant_id: UUID,
        platform_name: str,
        platform_id: str,
        platform_domain: str,
    ) -> dict:
        """Create credit account with platform context"""
        try:
            account = await self.prisma.creditaccount.create(
                data={
                    "merchant_id": str(merchant_id),
                    "platform_name": platform_name,
                    "platform_id": platform_id,
                    "platform_domain": platform_domain,
                    "balance": 0,
                    "total_granted": 0,
                    "total_consumed": 0,
                }
            )
            return account
        except UniqueViolationError:
            # Account already exists
            existing = await self.find_by_merchant_id(merchant_id)
            if existing:
                return existing
            raise

    async def find_by_merchant_id(self, merchant_id: UUID) -> dict | None:
        """Find credit account by merchant ID"""
        account = await self.prisma.creditaccount.find_unique(where={"merchant_id": str(merchant_id)})
        return account

    async def find_by_platform_domain(self, platform_domain: str) -> dict | None:
        """Find credit account by platform domain"""
        account = await self.prisma.creditaccount.find_first(where={"platform_domain": platform_domain})
        return account

    async def update_balance(
        self,
        merchant_id: UUID,
        amount: int,
        operation: str,  # 'credit' or 'debit'
        reference_type: str,
        reference_id: str,
        description: str | None = None,
        metadata: dict | None = None,
    ) -> tuple[dict, dict]:
        """
        Update balance with transaction record.
        Returns (account, transaction) tuple.
        Uses transaction to ensure consistency.
        """
        async with self.prisma.tx() as tx:
            # Get current account with lock
            account = await tx.creditaccount.find_unique(where={"merchant_id": str(merchant_id)})

            if not account:
                raise NotFoundError(
                    message=f"Credit account not found for merchant {merchant_id}",
                    resource="credit_account",
                    resource_id=str(merchant_id),
                )

            # Calculate new balance
            balance_before = account.balance
            if operation == "credit":
                balance_after = balance_before + amount
                total_granted = account.total_granted + amount
                total_consumed = account.total_consumed
            else:  # debit
                balance_after = max(0, balance_before - amount)  # Never negative
                actual_debit = balance_before - balance_after
                total_granted = account.total_granted
                total_consumed = account.total_consumed + actual_debit

            # Check for existing transaction (idempotency)
            existing_tx = await tx.credittransaction.find_unique(
                where={
                    "reference_type_reference_id": {
                        "reference_type": reference_type,
                        "reference_id": reference_id,
                    }
                }
            )

            if existing_tx:
                # Return existing without modification
                return account, existing_tx

            # Create transaction record
            transaction = await tx.credittransaction.create(
                data={
                    "account_id": account.id,
                    "merchant_id": str(merchant_id),
                    "amount": amount,
                    "operation": operation,
                    "balance_before": balance_before,
                    "balance_after": balance_after,
                    "reference_type": reference_type,
                    "reference_id": reference_id,
                    "description": description,
                    "metadata": metadata,
                }
            )

            # Update account balance
            account = await tx.creditaccount.update(
                where={"merchant_id": str(merchant_id)},
                data={
                    "balance": balance_after,
                    "total_granted": total_granted,
                    "total_consumed": total_consumed,
                },
            )

            return account, transaction

    async def get_transactions(self, merchant_id: UUID, skip: int = 0, take: int = 50) -> tuple[int, list[dict]]:
        """Get transaction history with pagination"""

        # Count total
        total = await self.prisma.credittransaction.count(where={"merchant_id": str(merchant_id)})

        # Get page
        transactions = await self.prisma.credittransaction.find_many(
            where={"merchant_id": str(merchant_id)},
            order_by={"created_at": "desc"},
            skip=skip,
            take=take,
        )

        return total, transactions
