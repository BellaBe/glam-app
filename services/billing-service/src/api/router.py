# services/billing-service/src/api/router.py
from fastapi import APIRouter


def create_main_router(
    billing_service: BillingService,
    trial_service: TrialService,
    purchase_service: OneTimePurchaseService,
    plan_repo: BillingPlanRepository
) -> APIRouter:
    """Create main API router"""
    
    router = APIRouter()
    
    # Include all sub-routers
    router.include_router(create_subscription_router(billing_service, trial_service))
    router.include_router(create_purchase_router(purchase_service))
    router.include_router(create_trial_router(trial_service))
    router.include_router(create_plans_router(plan_repo))
    
    return router
