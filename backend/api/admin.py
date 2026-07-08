"""Admin-only API endpoints for the DefenSync Admin Console."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.alerts import AlertResponse, AlertSummaryResponse
from backend.api.dependencies import get_current_admin, get_db
from backend.api.events import SecurityEventResponse
from backend.core.exceptions import ResourceNotFoundError, ValidationException
from backend.database import crud
from backend.database.models import User
from backend.services.admin_service import AdminService
from backend.services.alert_service import AlertService
from backend.services.event_service import EventService

logger = logging.getLogger(__name__)
router = APIRouter()


class AdminDashboardResponse(BaseModel):
    summary: dict[str, Any]
    charts: dict[str, Any]


class AdminUsersResponse(BaseModel):
    items: list[dict[str, Any]]
    total: int
    limit: int
    offset: int


class AdminEventsResponse(BaseModel):
    items: list[SecurityEventResponse]
    total: int
    limit: int
    offset: int


class AdminAlertItem(AlertResponse):
    server_name: str | None = None
    owner_username: str | None = None
    status: str


def get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    return AdminService(db)


@router.get("/dashboard", response_model=AdminDashboardResponse, summary="Admin dashboard summary and charts")
def admin_dashboard(
    current_admin: User = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> dict[str, Any]:
    del current_admin
    try:
        return {"summary": service.dashboard(), "charts": service.charts()}
    except Exception:
        logger.exception("Admin dashboard failed")
        raise


@router.get("/users", response_model=AdminUsersResponse, summary="List all users with platform stats")
def admin_list_users(
    search: str | None = Query(None),
    limit: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_admin: User = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> dict[str, Any]:
    del current_admin
    try:
        return service.list_users_enriched(search=search, limit=limit, offset=offset)
    except Exception:
        logger.exception("Admin users list failed")
        raise


@router.get("/users/{user_id}", summary="User profile and activity")
def admin_user_detail(
    user_id: str,
    current_admin: User = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> dict[str, Any]:
    del current_admin
    try:
        return service.user_detail(user_id)
    except ValueError as exc:
        raise ResourceNotFoundError(str(exc)) from exc
    except Exception:
        logger.exception("Admin user detail failed for user_id=%s", user_id)
        raise


@router.delete("/users/{user_id}", summary="Delete user")
def admin_delete_user(
    user_id: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if user_id == current_admin.id:
        raise ValidationException("You cannot delete your own account.")
    if not crud.delete_user(db, user_id):
        raise ResourceNotFoundError(f"User '{user_id}' not found.")
    db.commit()
    return {"success": True, "message": "User deleted."}


@router.get("/servers", summary="All registered servers")
def admin_list_servers(
    current_admin: User = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> list[dict[str, Any]]:
    del current_admin
    try:
        return service.list_servers_enriched()
    except Exception:
        logger.exception("Admin servers list failed")
        raise


@router.get("/events", response_model=AdminEventsResponse, summary="All security events")
def admin_list_events(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    severity: str | None = Query(None),
    event_type: str | None = Query(None),
    server_id: str | None = Query(None),
    owner_id: str | None = Query(None, description="Filter by owning user ID"),
    username: str | None = Query(None),
    search: str | None = Query(None),
    start_time: datetime | None = Query(None),
    end_time: datetime | None = Query(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    del current_admin
    try:
        service = EventService(db)
        items = service.query_events(
            limit=limit,
            offset=offset,
            severity=severity,
            event_type=event_type,
            server_id=server_id,
            owner_id=owner_id,
            username=username,
            search=search,
            start_time=start_time,
            end_time=end_time,
        )
        total = service.count_events(
            severity=severity,
            event_type=event_type,
            server_id=server_id,
            owner_id=owner_id,
            username=username,
            search=search,
            start_time=start_time,
            end_time=end_time,
        )
        return {"items": items, "total": total, "limit": limit, "offset": offset}
    except Exception:
        logger.exception("Admin events list failed")
        raise


@router.get("/alerts", response_model=list[AdminAlertItem], summary="All alerts")
def admin_list_alerts(
    limit: int = Query(500, ge=1, le=1000),
    acknowledged: bool | None = Query(None),
    current_admin: User = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> list[dict[str, Any]]:
    del current_admin
    try:
        return service.list_alerts_enriched(limit=limit, acknowledged=acknowledged)
    except Exception:
        logger.exception("Admin alerts list failed")
        raise


@router.get("/alerts/summary", response_model=AlertSummaryResponse, summary="Global alert summary")
def admin_alert_summary(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    del current_admin
    try:
        return AlertService(db).summary(owner_id=None)
    except Exception:
        logger.exception("Admin alert summary failed")
        raise


@router.get("/detections", summary="All ML detections")
def admin_detections(
    limit: int = Query(100, ge=1, le=500),
    current_admin: User = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> list[dict[str, Any]]:
    del current_admin
    try:
        return service.list_detections(limit=limit)
    except Exception:
        logger.exception("Admin detections list failed")
        raise


@router.get("/detections/status", summary="Global detection status")
def admin_detection_status(
    current_admin: User = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> dict[str, Any]:
    del current_admin
    try:
        return service.detection_summary()
    except Exception:
        logger.exception("Admin detection status failed")
        raise


@router.get("/collections", summary="All collection runs")
def admin_collections(
    limit: int = Query(200, ge=1, le=500),
    current_admin: User = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> list[dict[str, Any]]:
    del current_admin
    try:
        return service.list_collections(limit=limit)
    except Exception:
        logger.exception("Admin collections list failed")
        raise


@router.get("/analytics", summary="Global analytics")
def admin_analytics(
    current_admin: User = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> dict[str, Any]:
    del current_admin
    try:
        return service.analytics()
    except Exception:
        logger.exception("Admin analytics failed")
        raise


@router.get("/system-health", summary="Platform system health")
def admin_system_health(
    current_admin: User = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> dict[str, Any]:
    del current_admin
    try:
        return service.system_health()
    except Exception:
        logger.exception("Admin system health failed")
        raise


@router.get("/ml", summary="Machine learning platform stats")
def admin_ml(
    current_admin: User = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> dict[str, Any]:
    del current_admin
    try:
        return service.ml_stats()
    except Exception:
        logger.exception("Admin ML stats failed")
        raise
