from uuid import UUID

from fastapi import APIRouter

from shared.api import ApiResponse, success_response
from shared.api.dependencies import ClientAuthDep, RequestContextDep

from ...dependencies import BillingServiceDep
from ...schemas.billing import BillingStatusOut

billing_router = APIRouter()


@billing_router.get(
    "{merchant_id}",
    response_model=ApiResponse[BillingStatusOut],
    summary="Get overall billing status",
)
async def get_billing_status(
    billing_service: BillingServiceDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
):
    """Get overall billing status for merchant"""
    merchant_id = UUID(auth.shop)

    result = await billing_service.get_billing_status(merchant_id)

    return success_response(data=result, request_id=ctx.request_id, correlation_id=ctx.correlation_id)
