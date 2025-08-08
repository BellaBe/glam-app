from typing import Optional, Tuple
from datetime import datetime
import redis.asyncio as redis
from shared.utils.logger import ServiceLogger
from shared.api.correlation import get_correlation_context
from ..config import ServiceConfig
from ..repositories.credit_repository import CreditRepository
from ..schemas.credit import (
    CreditGrantIn, CreditGrantOut, BalanceOut, 
    LedgerOut, LedgerEntryOut
)
from ..events.publishers import CreditEventPublisher
from ..exceptions import (
    InvalidDomainError, InvalidAmountError, 
    MerchantCreditNotFoundError
)
from ..utils import normalize_shop_domain

class CreditService:
    """Pure business logic for credit management"""
    
    def __init__(
        self,
        config: ServiceConfig,
        repository: CreditRepository,
        publisher: CreditEventPublisher,
        logger: ServiceLogger,
        redis_client: Optional[redis.Redis] = None
    ):
        self.config = config
        self.repository = repository
        self.publisher = publisher
        self.logger = logger
        self.redis = redis_client
    
    async def grant_credits(
        self, 
        dto: CreditGrantIn, 
        ctx
    ) -> CreditGrantOut:
        """Grant credits to a merchant"""
        self.logger.info(
            f"Granting {dto.amount} credits to {dto.shop_domain}",
            extra={
                "correlation_id": ctx.correlation_id,
                "shop_domain": dto.shop_domain,
                "amount": dto.amount,
                "reason": dto.reason,
                "external_ref": dto.external_ref
            }
        )
        
        # Validate domain
        try:
            shop_domain = normalize_shop_domain(dto.shop_domain)
        except ValueError as e:
            raise InvalidDomainError(dto.shop_domain)
        
        # Validate amount
        if dto.amount <= 0:
            raise InvalidAmountError(dto.amount)
        
        # Get old balance for threshold checking
        old_balance_data = await self.repository.get_balance(shop_domain)
        old_balance = old_balance_data.balance if old_balance_data else 0
        
        # Grant credits (handles idempotency)
        new_balance, was_idempotent = await self.repository.grant_credits_transactional(
            shop_domain=shop_domain,
            amount=dto.amount,
            reason=dto.reason,
            external_ref=dto.external_ref,
            metadata=dto.metadata
        )
        
        if was_idempotent:
            self.logger.info(
                f"Grant already processed (idempotent): {dto.external_ref}",
                extra={
                    "correlation_id": ctx.correlation_id,
                    "external_ref": dto.external_ref
                }
            )
            return CreditGrantOut(ok=True, balance=new_balance, idempotent=True)
        
        # Check thresholds
        await self._check_balance_thresholds(
            shop_domain, old_balance, new_balance, ctx
        )
        
        # Publish balance changed event
        await self.publisher.balance_changed(
            shop_domain=shop_domain,
            delta=dto.amount,
            new_balance=new_balance,
            reason=dto.reason,
            external_ref=dto.external_ref,
            correlation_id=ctx.correlation_id
        )
        
        # Invalidate cache
        await self._invalidate_cache(shop_domain)
        
        self.logger.info(
            f"Credits granted successfully: {shop_domain} balance={new_balance}",
            extra={
                "correlation_id": ctx.correlation_id,
                "shop_domain": shop_domain,
                "new_balance": new_balance
            }
        )
        
        return CreditGrantOut(ok=True, balance=new_balance)
    
    async def get_balance(self, shop_domain: str) -> BalanceOut:
        """Get merchant credit balance with caching"""
        shop_domain = normalize_shop_domain(shop_domain)
        
        # Try cache first
        if self.redis and self.config.cache_enabled:
            cached = await self._get_cached_balance(shop_domain)
            if cached:
                return cached
        
        # Get from database
        balance = await self.repository.get_balance(shop_domain)
        if not balance:
            # Create default account
            await self.repository.get_or_create_merchant_credit(shop_domain)
            balance = BalanceOut(balance=0, updated_at=datetime.utcnow())
        
        # Cache result
        if self.redis and self.config.cache_enabled:
            await self._cache_balance(shop_domain, balance)
        
        return balance
    
    async def get_ledger(self, shop_domain: str) -> LedgerOut:
        """Get ledger entries for audit"""
        shop_domain = normalize_shop_domain(shop_domain)
        
        entries = await self.repository.get_ledger_entries(shop_domain)
        total = await self.repository.count_ledger_entries(shop_domain)
        
        return LedgerOut(entries=entries, total=total)
    
    async def _check_balance_thresholds(
        self, 
        shop_domain: str, 
        old_balance: int, 
        new_balance: int,
        ctx
    ) -> None:
        """Check and publish threshold events"""
        low_threshold = self.config.low_balance_threshold
        
        # Low balance crossed
        if old_balance > low_threshold and new_balance <= low_threshold:
            await self.publisher.balance_low(
                shop_domain=shop_domain,
                balance=new_balance,
                threshold=low_threshold,
                correlation_id=ctx.correlation_id
            )
            
            self.logger.warning(
                f"Low balance alert: {shop_domain} balance={new_balance}",
                extra={
                    "correlation_id": ctx.correlation_id,
                    "shop_domain": shop_domain,
                    "balance": new_balance
                }
            )
        
        # Balance depleted
        if old_balance > 0 and new_balance == 0:
            await self.publisher.balance_depleted(
                shop_domain=shop_domain,
                correlation_id=ctx.correlation_id
            )
            
            self.logger.warning(
                f"Balance depleted: {shop_domain}",
                extra={
                    "correlation_id": ctx.correlation_id,
                    "shop_domain": shop_domain
                }
            )
    
    async def _get_cached_balance(self, shop_domain: str) -> Optional[BalanceOut]:
        """Get balance from cache"""
        if not self.redis:
            return None
        
        try:
            key = f"balance:{shop_domain}"
            cached = await self.redis.get(key)
            if cached:
                import json
                data = json.loads(cached)
                return BalanceOut(
                    balance=data['balance'],
                    updated_at=datetime.fromisoformat(data['updated_at'])
                )
        except Exception as e:
            self.logger.error(f"Cache read error: {e}", exc_info=True)
        
        return None
    
    async def _cache_balance(self, shop_domain: str, balance: BalanceOut) -> None:
        """Cache balance with TTL"""
        if not self.redis:
            return
        
        try:
            key = f"balance:{shop_domain}"
            import json
            data = {
                'balance': balance.balance,
                'updated_at': balance.updated_at.isoformat()
            }
            await self.redis.setex(
                key, 
                self.config.cache_ttl_seconds,
                json.dumps(data)
            )
        except Exception as e:
            self.logger.error(f"Cache write error: {e}", exc_info=True)
    
    async def _invalidate_cache(self, shop_domain: str) -> None:
        """Invalidate cached balance"""
        if not self.redis:
            return
        
        try:
            key = f"balance:{shop_domain}"
            await self.redis.delete(key)
        except Exception as e:
            self.logger.error(f"Cache invalidation error: {e}", exc_info=True)

