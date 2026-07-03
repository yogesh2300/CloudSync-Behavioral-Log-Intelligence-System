"""REST API endpoints for dashboard analytics and security telemetry."""
from __future__ import annotations

import logging
from typing import Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.api import get_db
from backend.services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    """Dependency provider for DashboardService."""
    return DashboardService(db)


@router.get("/summary", status_code=status.HTTP_200_OK, summary="Get Dashboard Summary Metrics")
def get_dashboard_summary(
    service: DashboardService = Depends(get_dashboard_service),
) -> dict[str, Any]:
    """Placeholder endpoint returning aggregated metrics for SIEM dashboard visualization."""
    logger.info("API request: dashboard summary metrics")
    metrics = service.get_summary_metrics()
    return {
        "message": "Dashboard summary foundation active",
        "metrics": metrics,
    }