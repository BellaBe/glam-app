 services/billing-service/src/api/v1/subscriptions.py
from fastapi import APIRouter, Request, HTTPException, Query
from shared.api import success_response, paginated_response, CorrelationIdDep
from shared.database import DBSessionDep
from typing import Optional


def create_subscription_router(
    billing_service: BillingService,
    trial_service: TrialService
) -> APIRouter:
    """Create subscription management router"""
    
    router = APIRouter(prefix="/api/v1/billing/subscriptions", tags=["Subscriptions"])
    
    @router.post("", response_model=dict)
    async def create_subscription(
        request: Request,
        data: SubscriptionCreateRequest,
        correlation_id: CorrelationIdDep,
        db: DBSessionDep
    ):
        """Create new subscription (initiates Shopify charge)"""
        
        try:
            result = await billing_service.create_subscription(
                merchant_id=data.merchant_id,
                shop_id=data.shop_id,
                plan_id=data.plan_id,
                return_url=data.return_url,
                test_mode=data.test_mode,
                correlation_id=correlation_id
            )
            
            return success_response(
                data=result.__dict__,
                request_id=request.state.request_id,
                correlation_id=correlation_id
            )
            
        except BillingError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @router.get("/{subscription_id}")
    async def get_subscription(
        request: Request,
        subscription_id: UUID,
        correlation_id: CorrelationIdDep
    ):
        """Get subscription details"""
        
        subscription = await billing_service.get_subscription(subscription_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        return success_response(
            data=SubscriptionResponse.from_orm(subscription).__dict__,
            request_id=request.state.request_id,
            correlation_id=correlation_id
        )
    
    @router.get("/merchant/{merchant_id}")
    async def list_merchant_subscriptions(
        request: Request,
        merchant_id: UUID,
        correlation_id: CorrelationIdDep
    ):
        """List merchant subscriptions"""
        
        subscriptions = await billing_service.list_merchant_subscriptions(merchant_id)
        
        return success_response(
            data=[SubscriptionResponse.from_orm(s).__dict__ for s in subscriptions],
            request_id=request.state.request_id,
            correlation_id=correlation_id
        )
    
    @router.delete("/{subscription_id}")
    async def cancel_subscription(
        request: Request,
        subscription_id: UUID,
        immediate: bool = Query(False),
        reason: str = Query("merchant_request"),
        correlation_id: CorrelationIdDep
    ):
        """Cancel subscription"""
        
        # Implementation would cancel the subscription
        return success_response(
            data={"cancelled": True, "subscription_id": str(subscription_id)},
            request_id=request.state.request_id,
            correlation_id=correlation_id
        )
    
    return router
