
from uuid import UUID
from fastapi import APIRouter, status, Body
from shared.api import ApiResponse, success_response
from shared.api.dependencies import RequestContextDep, ClientAuthDep, PlatformContextDep
from shared.utils.exceptions import NotFoundError
from ...dependencies import BillingServiceDep
from ...schemas.billing import TrialActivateIn, TrialStatusOut, TrialActivatedOut
from ...exceptions import TrialAlreadyUsedError, MerchantNotFoundError


router = APIRouter(prefix="/api/billing/trials", tags=["Trials"])


@router.post(
    "",
    response_model=ApiResponse[TrialActivatedOut],
    status_code=status.HTTP_201_CREATED,
    summary="Activate trial"
)
async def activate_trial(
    billing_service: BillingServiceDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    platform: PlatformContextDep,
    body: TrialActivateIn = Body(None)
):
    """Activate trial for merchant"""
    # Use shop domain as merchant ID for now
    merchant_id = UUID(auth.shop)  # In production, lookup merchant by domain
    
    result = await billing_service.activate_trial(
        merchant_id=merchant_id,
        idempotency_key=body.idempotency_key if body else None
    )
    
    return success_response(
        data=result,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )


@router.get(
    "",
    response_model=ApiResponse[TrialStatusOut],
    summary="Get trial status"
)
async def get_trial_status(
    billing_service: BillingServiceDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    platform: PlatformContextDep
):
    """Get trial status for merchant"""
    merchant_id = UUID(auth.shop)
    
    result = await billing_service.get_trial_status(merchant_id)
    
    return success_response(
        data=result,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )


