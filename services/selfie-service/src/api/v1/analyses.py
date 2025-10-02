# services/selfie-service/src/api/v1/analyses.py
import json

from fastapi import APIRouter, BackgroundTasks, File, Form, Header, Response, UploadFile, status
from fastapi.responses import JSONResponse

from shared.api import ApiResponse, success_response
from shared.api.dependencies import PlatformContextDep, RequestContextDep
from shared.api.validation import validate_shop_context

from ...dependencies import ClientAuthDep, EventPublisherDep, LoggerDep, SelfieServiceDep
from ...schemas.analysis import AnalysisOut

router = APIRouter(prefix="/api/v1/analyses", tags=["Analyses"])


@router.post(
    "", response_model=ApiResponse[AnalysisOut], status_code=status.HTTP_202_ACCEPTED, summary="Create selfie analysis"
)
async def create_analysis(
    svc: SelfieServiceDep,
    publisher: EventPublisherDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    platform: PlatformContextDep,
    logger: LoggerDep,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Selfie image"),
    metadata: str = Form(..., description="JSON metadata"),
):
    """
    Create new selfie analysis.
    Direct multipart upload from widget.
    """
    # Validate shop context
    validate_shop_context(client_auth=auth, platform_ctx=platform, logger=logger, expected_scope="selfie:write")

    # Parse metadata
    try:
        meta = json.loads(metadata)
    except json.JSONDecodeError:
        from shared.utils.exceptions import ValidationError

        raise ValidationError(message="Invalid metadata JSON", field="metadata")

    # Read image bytes
    image_bytes = await file.read()

    # Create or get existing analysis
    analysis, is_new = await svc.create_analysis(
        merchant_id=auth.merchant_id,
        platform_name=platform.platform,
        platform_shop_id=auth.platform_shop_id,
        domain=platform.domain,
        image_bytes=image_bytes,
        metadata=meta,
        correlation_id=ctx.correlation_id,
    )

    # If new, queue background AI processing
    if is_new and hasattr(analysis, "_image_data"):
        background_tasks.add_task(
            svc.process_ai_analysis,
            analysis_id=analysis.id,
            image_jpeg_b64=analysis._image_data,
            correlation_id=ctx.correlation_id,
        )

        # Publish event
        await publisher.analysis_started(analysis)

    # Return appropriate status
    status_code = status.HTTP_200_OK if not is_new else status.HTTP_202_ACCEPTED

    response = success_response(data=analysis, request_id=ctx.request_id, correlation_id=ctx.correlation_id)

    # Add links
    response.links = {"self": f"/api/v1/analyses/{analysis.id}", "status": f"/api/v1/analyses/{analysis.id}/status"}

    return JSONResponse(content=response.model_dump(mode="json", exclude_none=True), status_code=status_code)


@router.get("/{analysis_id}/status", summary="Get analysis status")
async def get_analysis_status(
    analysis_id: str,
    svc: SelfieServiceDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    platform: PlatformContextDep,
    logger: LoggerDep,
    if_none_match: str | None = Header(None),
):
    """Get analysis status with ETag support for efficient polling"""

    # Validate shop context
    validate_shop_context(client_auth=auth, platform_ctx=platform, logger=logger, expected_scope="selfie:read")

    # Get status
    status_data = await svc.get_analysis_status(analysis_id=analysis_id, merchant_id=auth.merchant_id)

    # Generate ETag
    updated_at = status_data["updated_at"]
    etag = f'W/"{analysis_id}-{int(updated_at.timestamp())}-{status_data["status"]}"'

    # Check if client has current version
    if if_none_match == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED)

    # Return status with ETag
    return JSONResponse(
        content={
            "id": analysis_id,
            "status": status_data["status"],
            "progress": status_data["progress"],
            "message": status_data["message"],
        },
        headers={"ETag": etag},
    )


@router.get("/{analysis_id}", response_model=ApiResponse[AnalysisOut], summary="Get analysis details")
async def get_analysis(
    analysis_id: str,
    svc: SelfieServiceDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    platform: PlatformContextDep,
    logger: LoggerDep,
):
    """Get full analysis details"""

    # Validate shop context
    validate_shop_context(client_auth=auth, platform_ctx=platform, logger=logger, expected_scope="selfie:read")

    analysis = await svc.get_analysis(analysis_id=analysis_id, merchant_id=auth.merchant_id)

    return success_response(data=analysis, request_id=ctx.request_id, correlation_id=ctx.correlation_id)


@router.post("/claim", response_model=ApiResponse[dict], summary="Claim anonymous analyses")
async def claim_analyses(
    svc: SelfieServiceDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    platform: PlatformContextDep,
    logger: LoggerDep,
    customer_id: str = Form(...),
    anonymous_id: str = Form(...),
):
    """Link anonymous analyses to customer account"""

    # Validate shop context
    validate_shop_context(client_auth=auth, platform_ctx=platform, logger=logger, expected_scope="selfie:write")

    count = await svc.claim_analyses(
        merchant_id=auth.merchant_id,
        customer_id=customer_id,
        anonymous_id=anonymous_id,
        correlation_id=ctx.correlation_id,
    )

    return success_response(data={"claimed": count}, request_id=ctx.request_id, correlation_id=ctx.correlation_id)
