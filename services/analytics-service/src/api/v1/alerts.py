from uuid import UUID
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Path, Query, Body, status, HTTPException
from shared.api import ApiResponse, success_response, RequestContextDep
from ...services.alert_service import AlertService
from ...dependencies import AlertServiceDep
from ...schemas.analytics import (
    AlertRuleIn, AlertRulePatch, AlertRuleOut, AlertHistoryOut
)
from ...models.enums import AlertStatus
from ...exceptions import AlertNotFoundError

router = APIRouter(prefix="/api/v1", tags=["Alerts"])

# ========== Alert Rule Management ==========

@router.post(
    "/merchants/{merchant_id}/analytics/alerts/rules",
    response_model=ApiResponse[AlertRuleOut],
    status_code=status.HTTP_201_CREATED,
    summary="Create alert rule"
)
async def create_alert_rule(
    svc: AlertServiceDep,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    body: AlertRuleIn = Body(...)
):
    """Create new alert rule for merchant"""
    alert_rule = await svc.create_alert_rule(merchant_id, body)
    return success_response(alert_rule, ctx.request_id, ctx.correlation_id)

@router.get(
    "/merchants/{merchant_id}/analytics/alerts/rules",
    response_model=ApiResponse[List[AlertRuleOut]],
    summary="List alert rules"
)
async def list_alert_rules(
    svc: AlertServiceDep,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...)
):
    """List all alert rules for merchant"""
    rules = await svc.list_alert_rules(merchant_id)
    return success_response(rules, ctx.request_id, ctx.correlation_id)

@router.get(
    "/merchants/{merchant_id}/analytics/alerts/rules/{rule_id}",
    response_model=ApiResponse[AlertRuleOut],
    summary="Get alert rule"
)
async def get_alert_rule(
    svc: AlertServiceDep,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    rule_id: UUID = Path(...)
):
    """Get specific alert rule"""
    try:
        rule = await svc.get_alert_rule(rule_id)
        return success_response(rule, ctx.request_id, ctx.correlation_id)
    except AlertNotFoundError:
        raise HTTPException(404, "Alert rule not found")

@router.put(
    "/merchants/{merchant_id}/analytics/alerts/rules/{rule_id}",
    response_model=ApiResponse[AlertRuleOut],
    summary="Update alert rule"
)
async def update_alert_rule(
    svc: AlertServiceDep,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    rule_id: UUID = Path(...),
    body: AlertRulePatch = Body(...)
):
    """Update alert rule"""
    try:
        rule = await svc.update_alert_rule(rule_id, body)
        return success_response(rule, ctx.request_id, ctx.correlation_id)
    except AlertNotFoundError:
        raise HTTPException(404, "Alert rule not found")

@router.delete(
    "/merchants/{merchant_id}/analytics/alerts/rules/{rule_id}",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Delete alert rule"
)
async def delete_alert_rule(
    svc: AlertServiceDep,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    rule_id: UUID = Path(...)
):
    """Delete alert rule"""
    try:
        await svc.delete_alert_rule(rule_id)
        return success_response(
            {"message": "Alert rule deleted", "rule_id": str(rule_id)},
            ctx.request_id,
            ctx.correlation_id
        )
    except AlertNotFoundError:
        raise HTTPException(404, "Alert rule not found")

@router.post(
    "/merchants/{merchant_id}/analytics/alerts/rules/{rule_id}/test",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Test alert rule"
)
async def test_alert_rule(
    svc: AlertServiceDep,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    rule_id: UUID = Path(...),
    test_data: Dict[str, Any] = Body(...)
):
    """Test alert rule without triggering notifications"""
    try:
        result = await svc.test_alert_rule(rule_id, test_data)
        return success_response(result, ctx.request_id, ctx.correlation_id)
    except AlertNotFoundError:
        raise HTTPException(404, "Alert rule not found")

# ========== Alert Templates ==========

@router.get(
    "/analytics/alerts/templates",
    response_model=ApiResponse[List[Dict[str, Any]]],
    summary="Get alert templates"
)
async def get_alert_templates(
    svc: AlertServiceDep,
    ctx: RequestContextDep
):
    """Get pre-configured alert templates"""
    templates = await svc.get_alert_templates()
    return success_response(templates, ctx.request_id, ctx.correlation_id)

# ========== Alert Monitoring ==========

@router.get(
    "/merchants/{merchant_id}/analytics/alerts/active",
    response_model=ApiResponse[List[AlertHistoryOut]],
    summary="Get active alerts"
)
async def get_active_alerts(
    svc: AlertServiceDep,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    severity: Optional[str] = Query(None, regex="^(low|medium|high|critical)$"),
    status: Optional[str] = Query("active", regex="^(active|acknowledged|resolved)$")
):
    """Get active alerts for merchant"""
    if status == "active":
        alerts = await svc.get_active_alerts(merchant_id)
    else:
        alert_status = AlertStatus(status) if status else None
        alerts = await svc.get_alert_history(merchant_id, alert_status)
    
    # Filter by severity if specified
    if severity:
        alerts = [a for a in alerts if a.severity == severity]
    
    return success_response(alerts, ctx.request_id, ctx.correlation_id)

@router.get(
    "/merchants/{merchant_id}/analytics/alerts/history",
    response_model=ApiResponse[List[AlertHistoryOut]],
    summary="Get alert history"
)
async def get_alert_history(
    svc: AlertServiceDep,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    start_date: Optional[str] = Query(None),
    types: Optional[str] = Query(None, description="Comma-separated alert types"),
    limit: int = Query(50, ge=1, le=500)
):
    """Get alert history with optional filtering"""
    alerts = await svc.get_alert_history(merchant_id, limit=limit)
    
    # Filter by types if specified
    if types:
        type_list = types.split(",")
        alerts = [a for a in alerts if a.alert_type in type_list]
    
    return success_response(alerts, ctx.request_id, ctx.correlation_id)

@router.get(
    "/merchants/{merchant_id}/analytics/alerts/{alert_id}",
    response_model=ApiResponse[AlertHistoryOut],
    summary="Get alert details"
)
async def get_alert_details(
    svc: AlertServiceDep,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    alert_id: UUID = Path(...)
):
    """Get detailed information about specific alert"""
    try:
        alert = await svc.get_alert_history_by_id(alert_id)
        return success_response(alert, ctx.request_id, ctx.correlation_id)
    except AlertNotFoundError:
        raise HTTPException(404, "Alert not found")

# ========== Alert Actions ==========

@router.post(
    "/merchants/{merchant_id}/analytics/alerts/{alert_id}/acknowledge",
    response_model=ApiResponse[AlertHistoryOut],
    summary="Acknowledge alert"
)
async def acknowledge_alert(
    svc: AlertServiceDep,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    alert_id: UUID = Path(...),
    body: Dict[str, Any] = Body(...)
):
    """Acknowledge an active alert"""
    acknowledged_by = body.get("acknowledged_by", "system")
    
    try:
        alert = await svc.acknowledge_alert(alert_id, acknowledged_by)
        return success_response(alert, ctx.request_id, ctx.correlation_id)
    except AlertNotFoundError:
        raise HTTPException(404, "Alert not found")
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post(
    "/merchants/{merchant_id}/analytics/alerts/{alert_id}/resolve",
    response_model=ApiResponse[AlertHistoryOut],
    summary="Resolve alert"
)
async def resolve_alert(
    svc: AlertServiceDep,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    alert_id: UUID = Path(...),
    body: Dict[str, Any] = Body(...)
):
    """Resolve an alert"""
    resolved_by = body.get("resolved_by", "system")
    resolution_notes = body.get("resolution_notes")
    
    try:
        alert = await svc.resolve_alert(alert_id, resolved_by, resolution_notes)
        return success_response(alert, ctx.request_id, ctx.correlation_id)
    except AlertNotFoundError:
        raise HTTPException(404, "Alert not found")
    except Exception as e:
        raise HTTPException(400, str(e))


