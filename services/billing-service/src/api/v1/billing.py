from uuid import UUID
from typing import List
from datetime import datetime
from fastapi import APIRouter, Path, Body, status, HTTPException
from shared.api import ApiResponse, success_response
from shared.api.dependencies import RequestContextDep
from ...dependencies import (
    BillingServiceDep, WebhookServiceDep, PublisherDep,
    ShopDomainDep, IdempotencyKeyDep, FrontendAuthDep, AdminAuthDep
)
from ...schemas.billing import (
    PlansListOut, TrialCreateIn, TrialOut, RedirectCreateIn, RedirectOut,
    EntitlementsOut, BillingStateOut, ReconcileIn, ReconcileOut,
    TrialExtendIn, TrialActivatedPayload
)
from ...exceptions import (
    InvalidDomainError, InvalidPlanError, InvalidReturnUrlError,
    TrialAlreadyUsedError, SubscriptionExistsError
)

router = APIRouter(prefix="/api/billing", tags=["Billing"])

@router.get(
    "/managed/plans",
    response_model=ApiResponse[PlansListOut],
    summary="Get billing plans",
    dependencies=[FrontendAuthDep]
)
async def get_billing_plans(
    svc: BillingServiceDep,
    ctx: RequestContextDep,
    shop_domain: ShopDomainDep,
):
    """Get active billing plans with trial status"""
    try:
        result = await svc.get_plans_with_trial_status(shop_domain)
        return success_response(
            result,
            ctx.request_id,
            ctx.correlation_id,
        )
    except InvalidDomainError as e:
        raise HTTPException(400, str(e))

@router.post(
    "/managed/redirect",
    response_model=ApiResponse[RedirectOut],
    summary="Create checkout redirect",
    dependencies=[FrontendAuthDep]
)
async def create_checkout_redirect(
    svc: BillingServiceDep,
    ctx: RequestContextDep,
    shop_domain: ShopDomainDep,
    idempotency_key: IdempotencyKeyDep,
    body: RedirectCreateIn = Body(...),
):
    """Generate Shopify managed checkout URL"""
    try:
        redirect_url = await svc.create_checkout_redirect(
            shop_domain,
            body.plan,
            str(body.returnUrl) if body.returnUrl else None
        )
        return success_response(
            RedirectOut(redirectUrl=redirect_url),
            ctx.request_id,
            ctx.correlation_id,
        )
    except InvalidDomainError as e:
        raise HTTPException(400, str(e))
    except InvalidPlanError as e:
        raise HTTPException(400, str(e))
    except InvalidReturnUrlError as e:
        raise HTTPException(400, str(e))
    except SubscriptionExistsError as e:
        raise HTTPException(409, str(e))

@router.post(
    "/trials",
    response_model=ApiResponse[TrialOut],
    summary="Create trial",
    status_code=status.HTTP_200_OK,
    dependencies=[FrontendAuthDep]
)
async def create_trial(
    svc: BillingServiceDep,
    publisher: PublisherDep,
    ctx: RequestContextDep,
    shop_domain: ShopDomainDep,
    idempotency_key: IdempotencyKeyDep,
    body: TrialCreateIn = Body(...),
):
    """Create or return existing trial"""
    try:
        result = await svc.activate_trial(
            shop_domain,
            body.days,
            idempotency_key,
            ctx
        )
        
        # Publish trial activated event if new
        if ctx.response.status_code == 201:
            payload = TrialActivatedPayload(
                shopDomain=shop_domain,
                endsAt=result.trialEndsAt,
                days=body.days or svc.config.default_trial_days,
                activatedAt=datetime.utcnow(),
                correlationId=ctx.correlation_id
            )
            await publisher.trial_activated(payload)
        
        return success_response(
            result,
            ctx.request_id,
            ctx.correlation_id,
        )
    except InvalidDomainError as e:
        raise HTTPException(400, str(e))
    except TrialAlreadyUsedError as e:
        raise HTTPException(409, str(e))

@router.get(
    "/trials/current",
    response_model=ApiResponse[TrialOut],
    summary="Get current trial",
    dependencies=[FrontendAuthDep]
)
async def get_current_trial(
    svc: BillingServiceDep,
    ctx: RequestContextDep,
    shop_domain: ShopDomainDep,
):
    """Get current trial status"""
    try:
        result = await svc.get_current_trial(shop_domain)
        return success_response(
            result,
            ctx.request_id,
            ctx.correlation_id,
        )
    except InvalidDomainError as e:
        raise HTTPException(400, str(e))

@router.get(
    "/entitlements/current",
    response_model=ApiResponse[EntitlementsOut],
    summary="Get current entitlements",
    dependencies=[FrontendAuthDep]
)
async def get_current_entitlements(
    svc: BillingServiceDep,
    ctx: RequestContextDep,
    shop_domain: ShopDomainDep,
):
    """Get combined entitlements status"""
    try:
        result = await svc.calculate_entitlements(shop_domain)
        return success_response(
            result,
            ctx.request_id,
            ctx.correlation_id,
        )
    except InvalidDomainError as e:
        raise HTTPException(400, str(e))

@router.get(
    "/state",
    response_model=ApiResponse[BillingStateOut],
    summary="Get billing state",
    dependencies=[FrontendAuthDep]
)
async def get_billing_state(
    svc: BillingServiceDep,
    ctx: RequestContextDep,
    shop_domain: ShopDomainDep,
):
    """Get detailed billing state"""
    try:
        result = await svc.get_billing_state(shop_domain)
        return success_response(
            result,
            ctx.request_id,
            ctx.correlation_id,
        )
    except InvalidDomainError as e:
        raise HTTPException(400, str(e))

# Admin endpoints
@router.post(
    "/internal/reconcile",
    response_model=ApiResponse[ReconcileOut],
    summary="Reconcile billing",
    dependencies=[AdminAuthDep],
    include_in_schema=False
)
async def reconcile_billing(
    svc: BillingServiceDep,
    ctx: RequestContextDep,
    body: ReconcileIn = Body(...),
):
    """Force sync with Shopify (admin only)"""
    # TODO: Implement reconciliation with Token Service + Shopify Admin API
    return success_response(
        ReconcileOut(updated=False, changes=None),
        ctx.request_id,
        ctx.correlation_id,
    )

@router.post(
    "/internal/trials/extend",
    response_model=ApiResponse[dict],
    summary="Extend trial",
    dependencies=[AdminAuthDep],
    include_in_schema=False
)
async def extend_trial(
    svc: BillingServiceDep,
    ctx: RequestContextDep,
    body: TrialExtendIn = Body(...),
):
    """Extend trial for support purposes"""
    try:
        new_ends_at = await svc.extend_trial(body.shopDomain, body.days)
        return success_response(
            {"success": True, "newEndsAt": new_ends_at.isoformat()},
            ctx.request_id,
            ctx.correlation_id,
        )
    except Exception as e:
        raise HTTPException(400, str(e))

