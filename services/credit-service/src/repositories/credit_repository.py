from typing import Optional, List
from uuid import UUID
from datetime import datetime
from prisma import Prisma
from prisma.models import MerchantCredit, CreditLedger
from ..schemas.credit import CreditGrantIn, LedgerEntryOut, BalanceOut
from ..utils import normalize_shop_domain

class CreditRepository:
    """Repository for credit operations using Prisma"""
    
    def __init__(self, prisma: Prisma):
        self.prisma = prisma
    
    async def get_or_create_merchant_credit(self, shop_domain: str) -> MerchantCredit:
        """Get or create merchant credit account"""
        shop_domain = normalize_shop_domain(shop_domain)
        
        # Try to get existing
        merchant = await self.prisma.merchantcredit.find_unique(
            where={"shopDomain": shop_domain}
        )
        
        if not merchant:
            # Create new with default balance
            merchant = await self.prisma.merchantcredit.create(
                data={"shopDomain": shop_domain, "balance": 0}
            )
        
        return merchant
    
    async def find_ledger_by_external_ref(self, external_ref: str) -> Optional[CreditLedger]:
        """Find ledger entry by external reference"""
        return await self.prisma.creditledger.find_unique(
            where={"externalRef": external_ref}
        )
    
    async def grant_credits_transactional(
        self, 
        shop_domain: str, 
        amount: int, 
        reason: str,
        external_ref: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> tuple[int, bool]:  # (new_balance, was_idempotent)
        """Grant credits in a transaction with row locking"""
        shop_domain = normalize_shop_domain(shop_domain)
        
        # Check for existing grant (idempotency)
        if external_ref:
            existing = await self.find_ledger_by_external_ref(external_ref)
            if existing:
                # Get current balance
                merchant = await self.get_or_create_merchant_credit(shop_domain)
                return merchant.balance, True
        
        # Execute in transaction
        async with self.prisma.tx() as tx:
            # Get or create with lock
            merchant = await tx.merchantcredit.upsert(
                where={"shopDomain": shop_domain},
                create={"shopDomain": shop_domain, "balance": 0},
                update={}
            )
            
            # Create ledger entry
            await tx.creditledger.create(
                data={
                    "shopDomain": shop_domain,
                    "amount": amount,
                    "reason": reason,
                    "externalRef": external_ref,
                    "metadata": metadata
                }
            )
            
            # Update balance
            updated = await tx.merchantcredit.update(
                where={"shopDomain": shop_domain},
                data={"balance": {"increment": amount}}
            )
            
            return updated.balance, False
    
    async def get_balance(self, shop_domain: str) -> Optional[BalanceOut]:
        """Get merchant credit balance"""
        shop_domain = normalize_shop_domain(shop_domain)
        
        merchant = await self.prisma.merchantcredit.find_unique(
            where={"shopDomain": shop_domain}
        )
        
        if not merchant:
            return None
        
        return BalanceOut(
            balance=merchant.balance,
            updated_at=merchant.updatedAt
        )
    
    async def get_ledger_entries(self, shop_domain: str, limit: int = 100) -> List[LedgerEntryOut]:
        """Get ledger entries for a merchant"""
        shop_domain = normalize_shop_domain(shop_domain)
        
        entries = await self.prisma.creditledger.find_many(
            where={"shopDomain": shop_domain},
            order_by={"createdAt": "desc"},
            take=limit
        )
        
        return [
            LedgerEntryOut(
                id=entry.id,
                amount=entry.amount,
                reason=entry.reason,
                external_ref=entry.externalRef,
                metadata=entry.metadata,
                created_at=entry.createdAt
            )
            for entry in entries
        ]
    
    async def count_ledger_entries(self, shop_domain: str) -> int:
        """Count total ledger entries for a merchant"""
        shop_domain = normalize_shop_domain(shop_domain)
        
        return await self.prisma.creditledger.count(
            where={"shopDomain": shop_domain}
        )

