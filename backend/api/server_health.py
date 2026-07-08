"""Fleet health monitoring API — reads persisted probe results, never blocks on SSH."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.api.dependencies import get_current_user, get_db, resolve_owner_id, validate_server_scope
from backend.core.logging import get_logger
from backend.database import server_crud
from backend.database.models import User
from backend.services.health_engine import get_health_engine
from backend.services.server_service import ServerService

logger = get_logger(__name__)
router = APIRouter()


class FleetHealthResponse(BaseModel):
    total_servers: int = 0
    active_servers: int = 0
    online_servers: int = 0
    offline_servers: int = 0
    healthy_servers: int = 0
    servers_with_errors: int = 0
    average_ssh_latency_ms: int = 0
    recently_connected: int = 0
    recently_disconnected: int = 0
    engine_running: bool = False
    last_run_at: str | None = None


class HealthCheckTriggerResponse(BaseModel):
    accepted: bool
    status: str
    message: str
    last_run_at: str | None = None


@router.get("/servers", response_model=FleetHealthResponse, status_code=status.HTTP_200_OK)
def get_fleet_health(
    server_id: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return aggregated fleet health from the latest background probes."""
    owner_id = resolve_owner_id(current_user)
    scoped_server_id = validate_server_scope(server_id, current_user, db)
    summary = server_crud.health_summary(db, owner_id=owner_id, server_id=scoped_server_id)
    engine = get_health_engine()
    summary["engine_running"] = engine.is_running
    summary["last_run_at"] = engine.last_run_at.isoformat() if engine.last_run_at else None
    return summary


def get_server_service(db: Session = Depends(get_db)) -> ServerService:
    return ServerService(db)


@router.post("/servers/check", response_model=HealthCheckTriggerResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_fleet_health_check(
    server_id: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: ServerService = Depends(get_server_service),
) -> dict[str, Any]:
    """Queue a non-blocking health check cycle."""
    owner_id = resolve_owner_id(current_user)
    if server_id:
        validate_server_scope(server_id, current_user, db)
    logger.info("Manual health check queued by %s server_id=%s", current_user.username, server_id)
    return service.refresh_server_statuses(owner_id=owner_id, server_id=server_id)
