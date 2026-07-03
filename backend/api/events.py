"""REST API endpoints for security event querying and management."""
from __future__ import annotations

import logging
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.api import get_db
from backend.services.event_service import EventService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_event_service(db: Session = Depends(get_db)) -> EventService:
    """Dependency provider for EventService."""
    return EventService(db)


@router.get("/", status_code=status.HTTP_200_OK, summary="List Recent Security Events")
def list_events(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events to return"),
    service: EventService = Depends(get_event_service),
) -> dict[str, Any]:
    """Placeholder endpoint to retrieve recent security logs (Sprint 2 foundation)."""
    logger.info("API request: list recent events (limit=%d)", limit)
    events = service.list_recent_events(limit=limit)
    return {
        "message": "Security events endpoint foundation active",
        "count": len(events),
        "data": [
            {
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                "hostname": event.hostname,
                "username": event.username,
                "source_ip": event.source_ip,
                "event_type": event.event_type,
                "severity": event.severity,
                "risk_score": event.risk_score,
            }
            for event in events
        ],
    }


@router.get("/high-risk", status_code=status.HTTP_200_OK, summary="List High-Risk Security Events")
def list_high_risk_events(
    min_score: int = Query(70, ge=0, le=100, description="Minimum risk score threshold"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events to return"),
    service: EventService = Depends(get_event_service),
) -> dict[str, Any]:
    """Placeholder endpoint to retrieve high-risk security alerts."""
    logger.info("API request: list high-risk events (min_score=%d, limit=%d)", min_score, limit)
    events = service.list_high_risk_events(min_score=min_score, limit=limit)
    return {
        "message": "High-risk events endpoint active",
        "count": len(events),
        "data": [
            {
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                "hostname": event.hostname,
                "username": event.username,
                "source_ip": event.source_ip,
                "event_type": event.event_type,
                "severity": event.severity,
                "risk_score": event.risk_score,
            }
            for event in events
        ],
    }


@router.get("/{event_id}", status_code=status.HTTP_200_OK, summary="Get Event Details")
def get_event_detail(
    event_id: str,
    service: EventService = Depends(get_event_service),
) -> dict[str, Any]:
    """Placeholder endpoint to inspect a specific security event by ID."""
    logger.info("API request: get event detail for %s", event_id)
    event = service.get_event(event_id)
    if not event:
        return {"message": f"Event {event_id} not found", "data": None}
    return {
        "message": "Event details retrieved",
        "data": {
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            "hostname": event.hostname,
            "username": event.username,
            "source_ip": event.source_ip,
            "event_type": event.event_type,
            "category": event.category,
            "severity": event.severity,
            "risk_score": event.risk_score,
            "process": event.process,
            "message": event.message,
        },
    }