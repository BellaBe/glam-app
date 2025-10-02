# services/selfie-ai-analyzer/src/api/v1/analyze.py
import time
import hmac
import hashlib
from fastapi import APIRouter, Body, Header, HTTPException, status
from shared.api import ApiResponse, success_response
from shared.api.dependencies import RequestContextDep, InternalAuthDep
from shared.utils.exceptions import ValidationError
from ...dependencies import AnalysisServiceDep, ConfigDep
from ...schemas.analysis import AnalysisRequest, AnalysisResponse

router = APIRouter(prefix="/api/v1", tags=["Analysis"])

@router.post(
    "/analyze",
    response_model=ApiResponse[AnalysisResponse],
    status_code=status.HTTP_200_OK,
    summary="Analyze selfie for color seasons"
)
async def analyze_selfie(
    svc: AnalysisServiceDep,
    ctx: RequestContextDep,
    config: ConfigDep,
    auth: InternalAuthDep,  # Internal service auth
    x_signature: str | None = Header(None),
    body: AnalysisRequest = Body(...)
):
    """
    Analyze selfie image for seasonal color analysis.
    Internal endpoint called by Selfie Service only.
    """
    
    # Optional HMAC verification if signature provided
    if x_signature and config.hmac_secret:
        expected = hmac.new(
            config.hmac_secret.encode(),
            f"{body.analysis_id}{int(time.time())}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Allow some time skew
        valid = False
        for offset in range(-config.hmac_time_skew_seconds, config.hmac_time_skew_seconds):
            test_sig = hmac.new(
                config.hmac_secret.encode(),
                f"{body.analysis_id}{int(time.time() + offset)}".encode(),
                hashlib.sha256
            ).hexdigest()
            if hmac.compare_digest(x_signature, test_sig):
                valid = True
                break
        
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )
    
    # Process analysis
    result = await svc.analyze_selfie(
        request=body,
        correlation_id=ctx.correlation_id
    )
    
    # Return success response
    return success_response(
        data=result,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )

@router.get(
    "/model-versions",
    response_model=ApiResponse[dict],
    summary="Get model version information"
)
async def get_model_versions(
    ctx: RequestContextDep,
    auth: InternalAuthDep
):
    """Get current model versions"""
    
    versions = {
        "deepface": "4.0",
        "mediapipe": "0.10.9",
        "algorithm": "v1.0.0",
        "season_model": "16-season-v1"
    }
    
    return success_response(
        data=versions,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )