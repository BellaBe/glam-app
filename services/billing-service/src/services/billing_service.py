from uuid import UUID
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlparse
import redis.asyncio as redis
from shared.utils.logger import ServiceLogger
from shared.api.correlation import get_correlation_context
from ..config import ServiceConfig
from ..repositories.billing_plan_repository import BillingPlanRepository
from ..repositories.merchant_billing_repository import MerchantBillingRepository
from ..repositories.merchant_trial_repository import MerchantTrialRepository
from ..repositories.one_time_purchase_repository import OneTimePurchaseRepository
from ..schemas.billing import (
    BillingPlanOut, TrialOut, EntitlementsOut, BillingStateOut,
    PlansListOut, TrialStatus, SubscriptionStatus, EntitlementSource, EntitlementReason
)
from ..exceptions import (
    InvalidDomainError, InvalidPlanError, InvalidReturnUrlError,
    TrialAlreadyUsedError, SubscriptionExistsError
)

class BillingService:
    """Business logic for billing operations"""
    
    def __init__(
        self,
        config: ServiceConfig,
        plan_repo: BillingPlanRepository,
        billing_repo: MerchantBillingRepository,
        trial_repo: MerchantTrialRepository,
        purchase_repo: OneTimePurchaseRepository,
        redis_client: redis.Redis,
        logger: ServiceLogger,
    ):
        self.config = config
        self.plan_repo = plan_repo
        self.billing_repo = billing_repo
        self.trial_repo = trial_repo
        self.purchase_repo = purchase_repo
        self.redis = redis_client
        self.logger = logger
    
    def normalize_shop_domain(self, domain: str) -> str:
        """Normalize and validate shop domain"""
        normalized = domain.lower().strip()
        if not normalized.endswith('.myshopify.com'):
            raise InvalidDomainError(domain)
        return normalized
    
    async def get_plans_with_trial_status(self, shop_domain: str) -> PlansListOut:
        """Get active billing plans and trial usage status"""
        shop_domain = self.normalize_shop_domain(shop_domain)
        
        # Get active plans
        plans = await self.plan_repo.find_active_plans()
        
        # Check trial status
        trial = await self.trial_repo.find_by_shop_domain(shop_domain)
        trial_used = trial.consumed if trial else False
        
        return PlansListOut(plans=plans, trialUsed=trial_used)
    
    async def create_checkout_redirect(
        self, 
        shop_domain: str, 
        plan_id: str, 
        return_url: Optional[str] = None
    ) -> str:
        """Generate Shopify managed checkout URL"""
        shop_domain = self.normalize_shop_domain(shop_domain)
        
        # Validate plan exists
        plan = await self.plan_repo.find_by_id(plan_id)
        if not plan:
            raise InvalidPlanError(plan_id)
        
        # Validate return URL if provided
        if return_url:
            self._validate_return_url(str(return_url))
        
        # Check if already subscribed to this plan
        billing = await self.billing_repo.find_by_shop_domain(shop_domain)
        if (billing and 
            billing.subscriptionStatus == SubscriptionStatus.active and
            billing.managedPlanHandle == plan.shopifyHandle):
            raise SubscriptionExistsError(plan_id)
        
        # Build checkout URL
        return self._build_checkout_url(shop_domain, plan.shopifyHandle, return_url)
    
    def _validate_return_url(self, url: str) -> None:
        """Validate return URL against allowlist"""
        parsed = urlparse(url)
        if parsed.hostname not in self.config.allowed_return_domains:
            raise InvalidReturnUrlError(url)
    
    def _build_checkout_url(
        self, 
        shop_domain: str, 
        plan_handle: str, 
        return_url: Optional[str] = None
    ) -> str:
        """Build Shopify managed checkout URL"""
        base_url = self.config.shopify_managed_checkout_base
        app_handle = self.config.app_handle
        
        url = f"{base_url}/{shop_domain}/apps/{app_handle}/pricing"
        params = [f"plan={plan_handle}"]
        
        if return_url:
            params.append(f"return_to={return_url}")
        
        return f"{url}?{'&'.join(params)}"
    
    async def activate_trial(
        self, 
        shop_domain: str, 
        days: Optional[int] = None,
        idempotency_key: Optional[str] = None,
        ctx: Any = None
    ) -> TrialOut:
        """Activate trial for merchant"""
        shop_domain = self.normalize_shop_domain(shop_domain)
        days = days or self.config.default_trial_days
        
        # Check idempotency
        if idempotency_key:
            cached = await self._get_idempotent_response(idempotency_key)
            if cached:
                return cached
        
        trial = await self.trial_repo.find_by_shop_domain(shop_domain)
        
        if not trial:
            # Create new trial
            trial = await self.trial_repo.create(shop_domain, days)
            response = self._format_trial_response(trial)
            status_code = 201
        elif trial.consumed:
            raise TrialAlreadyUsedError(shop_domain)
        elif trial.status == TrialStatus.active:
            # Return existing active trial
            response = self._format_trial_response(trial)
            status_code = 200
        else:
            # Activate never_started trial
            trial = await self.trial_repo.activate_existing(trial.id)
            response = self._format_trial_response(trial)
            status_code = 201
        
        # Cache response
        if idempotency_key:
            await self._set_idempotent_response(idempotency_key, response, status_code)
        
        return response
    
    async def get_current_trial(self, shop_domain: str) -> TrialOut:
        """Get current trial status"""
        shop_domain = self.normalize_shop_domain(shop_domain)
        
        trial = await self.trial_repo.find_by_shop_domain(shop_domain)
        if not trial:
            return TrialOut(status=TrialStatus.never_started)
        
        return self._format_trial_response(trial)
    
    def _format_trial_response(self, trial) -> TrialOut:
        """Format trial model into response DTO"""
        remaining_days = None
        if trial.status == TrialStatus.active and trial.endsAt:
            remaining = (trial.endsAt - datetime.utcnow()).days
            remaining_days = max(0, remaining)
        
        return TrialOut(
            status=trial.status,
            trialEndsAt=trial.endsAt,
            remainingDays=remaining_days
        )
    
    async def calculate_entitlements(self, shop_domain: str) -> EntitlementsOut:
        """Calculate merchant entitlements"""
        shop_domain = self.normalize_shop_domain(shop_domain)
        
        # Check cache first
        cache_key = f"entitlements:{shop_domain}"
        cached = await self.redis.get(cache_key)
        if cached:
            import json
            return EntitlementsOut(**json.loads(cached))
        
        billing = await self.billing_repo.find_by_shop_domain(shop_domain)
        trial = await self.trial_repo.find_by_shop_domain(shop_domain)
        
        # Check trial status
        trial_active = False
        if trial and trial.status == TrialStatus.active and trial.endsAt:
            trial_active = datetime.utcnow() < trial.endsAt
        
        # Check subscription status
        subscription_active = False
        if billing and billing.subscriptionStatus == SubscriptionStatus.active:
            if billing.currentPeriodEnd is None or datetime.utcnow() <= billing.currentPeriodEnd:
                subscription_active = True
        
        # Determine source and reason
        if subscription_active:
            source = EntitlementSource.subscription
            reason = None
        elif trial_active:
            source = EntitlementSource.trial
            reason = None
        else:
            source = EntitlementSource.none
            if trial and trial.consumed:
                reason = EntitlementReason.trial_expired
            elif billing and billing.subscriptionStatus == SubscriptionStatus.cancelled:
                reason = EntitlementReason.subscription_cancelled
            else:
                reason = EntitlementReason.no_subscription
        
        result = EntitlementsOut(
            trialActive=trial_active,
            subscriptionActive=subscription_active,
            entitled=subscription_active or trial_active,
            source=source,
            reason=reason,
            trialEndsAt=trial.endsAt if trial else None,
            currentPeriodEnd=billing.currentPeriodEnd if billing else None
        )
        
        # Cache result
        await self.redis.setex(
            cache_key,
            self.config.entitlements_cache_ttl_seconds,
            result.model_dump_json()
        )
        
        return result
    
    async def get_billing_state(self, shop_domain: str) -> BillingStateOut:
        """Get complete billing state for merchant"""
        shop_domain = self.normalize_shop_domain(shop_domain)
        
        billing = await self.billing_repo.find_by_shop_domain(shop_domain)
        trial = await self.trial_repo.find_by_shop_domain(shop_domain)
        
        # Get plan details if subscribed
        plan_name = None
        plan_id = None
        if billing and billing.managedPlanId:
            plan = await self.plan_repo.find_by_id(billing.managedPlanId)
            if plan:
                plan_name = plan.name
                plan_id = plan.id
        
        # Calculate trial info
        trial_info = {
            "used": trial.consumed if trial else False,
            "remainingDays": 0,
            "endsAt": None
        }
        
        if trial and trial.status == TrialStatus.active and trial.endsAt:
            remaining = (trial.endsAt - datetime.utcnow()).days
            trial_info["remainingDays"] = max(0, remaining)
            trial_info["endsAt"] = trial.endsAt.isoformat()
        
        return BillingStateOut(
            status=billing.subscriptionStatus if billing else SubscriptionStatus.none,
            planId=plan_id,
            planName=plan_name,
            planHandle=billing.managedPlanHandle if billing else None,
            trial=trial_info,
            currentPeriodEnd=billing.currentPeriodEnd if billing else None,
            lastUpdatedAt=billing.updatedAt if billing else datetime.utcnow()
        )
    
    async def extend_trial(self, shop_domain: str, days: int) -> datetime:
        """Extend trial for support purposes"""
        shop_domain = self.normalize_shop_domain(shop_domain)
        
        trial = await self.trial_repo.extend_trial(shop_domain, days)
        
        # Clear entitlements cache
        await self.redis.delete(f"entitlements:{shop_domain}")
        
        return trial.endsAt
    
    async def expire_trials(self) -> List[str]:
        """Expire trials that have ended (called by scheduler)"""
        expired_trials = await self.trial_repo.find_expired_trials()
        expired_domains = []
        
        for trial in expired_trials:
            await self.trial_repo.expire_trial(trial.id)
            expired_domains.append(trial.shopDomain)
            
            # Clear entitlements cache
            await self.redis.delete(f"entitlements:{trial.shopDomain}")
        
        return expired_domains
    
    async def _get_idempotent_response(self, key: str) -> Optional[Any]:
        """Get cached idempotent response"""
        cached = await self.redis.get(f"idem:{key}")
        if cached:
            import json
            data = json.loads(cached)
            if data["status"] >= 400:
                # Re-raise the error
                if data["error"] == "TRIAL_ALREADY_USED":
                    raise TrialAlreadyUsedError(data.get("shop_domain", ""))
            return TrialOut(**data["body"])
        return None
    
    async def _set_idempotent_response(self, key: str, response: Any, status_code: int) -> None:
        """Cache idempotent response"""
        data = {
            "status": status_code,
            "body": response.model_dump()
        }
        ttl = self.config.idempotency_ttl_hours * 3600
        await self.redis.setex(f"idem:{key}", ttl, json.dumps(data))

