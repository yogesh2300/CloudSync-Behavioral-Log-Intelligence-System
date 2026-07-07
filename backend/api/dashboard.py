"""REST API endpoints for dashboard analytics and SIEM metric summaries."""
from __future__ import annotations

from backend.core.logging import get_logger
from typing import Any
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.api.dependencies import get_current_user, get_db
from backend.database.models import User
from backend.services.dashboard_service import DashboardService

logger = get_logger(__name__)

router = APIRouter()


class DashboardSummaryResponse(BaseModel):
    """Pydantic schema representing aggregated dashboard telemetry summary metrics."""

    total_events: int = Field(..., description="Total number of recorded security events")
    high_risk: int = Field(..., description="Count of high-risk security events (score >= 70)")
    successful_logins: int = Field(..., description="Count of successful authentication events")
    failed_logins: int = Field(..., description="Count of failed authentication events")
    unique_users: int = Field(..., description="Number of distinct usernames observed")
    unique_ips: int = Field(..., description="Number of distinct source IP addresses observed")
    average_risk_score: int = Field(0, description="Average risk score across all security events")
    total_servers: int = Field(0, description="Total registered Linux servers")
    active_servers: int = Field(0, description="Active monitored servers")
    online_servers: int = Field(0, description="Servers with online SSH status")
    offline_servers: int = Field(0, description="Active servers currently offline")


def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    """Dependency injection provider yielding a DashboardService bound to the current database session."""
    return DashboardService(db)


@router.get("/summary", response_model=DashboardSummaryResponse, status_code=status.HTTP_200_OK, summary="Get Dashboard Summary")
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service),
) -> Any:
    """Retrieve aggregated SIEM telemetry summary metrics for dashboard visualization."""
    logger.info("API request by %s: GET /dashboard/summary", current_user.username)
    owner_id = None if current_user.role.upper() == "ADMIN" else current_user.id
    try:
        return service.dashboard_summary(owner_id=owner_id)
    except Exception:
        logger.exception("Unhandled dashboard summary error; returning zero JSON response")
        return DashboardService.empty_summary()


@router.get("", response_model=DashboardSummaryResponse, status_code=status.HTTP_200_OK, summary="Get Dashboard Summary")
def get_dashboard_root(
    current_user: User = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service),
) -> Any:
    """Retrieve dashboard metrics at /api/v1/dashboard."""
    logger.info("API request by %s: GET /dashboard", current_user.username)
    owner_id = None if current_user.role.upper() == "ADMIN" else current_user.id
    try:
        return service.dashboard_summary(owner_id=owner_id)
    except Exception:
        logger.exception("Unhandled dashboard root error; returning zero JSON response")
        return DashboardService.empty_summary()