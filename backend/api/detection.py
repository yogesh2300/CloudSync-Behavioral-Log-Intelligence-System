"""REST API endpoints for ML behavioral detection."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.api.dependencies import get_current_user, get_db
from backend.core.logging import get_logger
from backend.database.models import User
from backend.services.detection_service import DetectionService

logger = get_logger(__name__)
router = APIRouter()


class DetectionRunResponse(BaseModel):
    success: bool
    events_analyzed: int
    rule_alerts_created: int = 0
    ml_anomalies: int = 0
    ml_classified_suspicious: int = 0
    total_flagged: int | None = None
    normal: int = 0
    suspicious: int = 0
    malicious: int = 0
    predictions_stored: int = 0
    message: str


class AnomalyItem(BaseModel):
    event_id: str
    timestamp: str | None
    hostname: str
    username: str | None
    source_ip: str | None
    server_id: str | None = None
    event_type: str
    severity: str
    risk_score: int
    message: str
    detection_type: str
    classification: str | None = None
    anomaly_score: float | None = None


def get_detection_service(db: Session = Depends(get_db)) -> DetectionService:
    return DetectionService(db)


@router.get("/status", summary="Detection engine status")
def detection_status(
    current_user: User = Depends(get_current_user),
    service: DetectionService = Depends(get_detection_service),
) -> Any:
    logger.info("API request by %s: GET /detection/status", current_user.username)
    owner_id = None if current_user.role.upper() == "ADMIN" else current_user.id
    return service.status(owner_id=owner_id)


@router.post("/run", response_model=DetectionRunResponse, summary="Run hybrid detection")
def run_detection(
    current_user: User = Depends(get_current_user),
    service: DetectionService = Depends(get_detection_service),
) -> Any:
    logger.info("API request by %s: POST /detection/run", current_user.username)
    owner_id = None if current_user.role.upper() == "ADMIN" else current_user.id
    return service.run_detection(owner_id=owner_id)


@router.get("/anomalies", response_model=list[AnomalyItem], summary="List detected anomalies")
def list_anomalies(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: DetectionService = Depends(get_detection_service),
) -> Any:
    logger.info("API request by %s: GET /detection/anomalies", current_user.username)
    owner_id = None if current_user.role.upper() == "ADMIN" else current_user.id
    return service.get_anomalies(limit=limit, owner_id=owner_id)
