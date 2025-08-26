# services/analytics/src/schemas/events.py
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# Consumed event payloads
class SelfieAnalysisCompletedPayload(BaseModel):
    """evt.selfie.analysis.completed payload"""
    merchant_id: UUID
    platform_name: str
    platform_shop_id: str
    platform_domain: str
    shopper_id: Optional[str] = None
    anonymous_id: Optional[str] = None
    analysis_id: str
    primary_season: str
    secondary_season: Optional[str] = None
    tertiary_season: Optional[str] = None
    confidence: float
    processing_time_ms: int
    status: str = "completed"
    analyzed_at: datetime

class RecommendationMatchCompletedPayload(BaseModel):
    """evt.recommendation.match.completed payload"""
    merchant_id: UUID
    platform_name: str
    platform_shop_id: str
    platform_domain: str
    match_id: str
    shopper_id: Optional[str] = None
    anonymous_id: Optional[str] = None
    analysis_id: str
    products_matched: List[dict]  # [{product_id, variant_id, score, season}]
    total_matches: int
    avg_match_score: float
    top_match_score: float
    primary_season: str
    credits_consumed: int = 1
    matched_at: datetime

class CreditsConsumedPayload(BaseModel):
    """evt.credits.consumed payload"""
    merchant_id: UUID
    platform_name: str
    platform_shop_id: str
    platform_domain: str
    credits_consumed: int
    operation: str
    operation_id: str
    remaining_balance: int
    consumed_at: datetime

class CreditsGrantedPayload(BaseModel):
    """evt.credits.granted payload"""
    merchant_id: UUID
    platform_name: str
    platform_shop_id: str
    platform_domain: str
    credits_granted: int
    reason: str
    new_balance: int
    granted_at: datetime

class CatalogSyncCompletedPayload(BaseModel):
    """evt.catalog.sync.completed payload"""
    merchant_id: UUID
    platform_name: str
    platform_shop_id: str
    platform_domain: str
    total_products: int
    analyzed_products: int
    sync_duration_ms: int
    synced_at: datetime

class MerchantCreatedPayload(BaseModel):
    """evt.merchant.created payload"""
    merchant_id: UUID
    platform_name: str
    platform_shop_id: str
    platform_domain: str
    plan: str
    created_at: datetime

class BillingTrialStartedPayload(BaseModel):
    """evt.billing.trial.started payload"""
    merchant_id: UUID
    platform_name: str
    platform_shop_id: str
    platform_domain: str
    trial_days: int
    trial_credits: int
    started_at: datetime

class BillingCreditsPurchasedPayload(BaseModel):
    """evt.billing.credits.purchased payload"""
    merchant_id: UUID
    platform_name: str
    platform_shop_id: str
    platform_domain: str
    credits_purchased: int
    amount_paid: float
    currency: str
    purchased_at: datetime