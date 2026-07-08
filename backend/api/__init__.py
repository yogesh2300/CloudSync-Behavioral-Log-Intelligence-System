"""API router aggregation for DefenSync."""

from __future__ import annotations

from fastapi import APIRouter

from backend.api.admin import router as admin_router
from backend.api.alerts import router as alerts_router
from backend.api.servers import router as servers_router
from backend.api.auth import router as auth_router
from backend.api.collection import router as collection_router
from backend.api.dashboard import router as dashboard_router
from backend.api.detection import router as detection_router
from backend.api.events import router as events_router
from backend.api.health import router as health_router
from backend.api.server_health import router as server_health_router


# =============================================================================
# Root API Router
# =============================================================================

api_router = APIRouter()

# -------------------------------------------------------------------------
# Health Endpoints
# -------------------------------------------------------------------------

api_router.include_router(
    health_router,
    tags=["Health"],
)

api_router.include_router(
    server_health_router,
    prefix="/api/v1/health",
    tags=["Server Health"],
)

# -------------------------------------------------------------------------
# Authentication Endpoints
# -------------------------------------------------------------------------

api_router.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

# -------------------------------------------------------------------------
# Security Events Endpoints
# -------------------------------------------------------------------------

api_router.include_router(
    events_router,
    prefix="/api/v1/events",
    tags=["Events"],
)

# -------------------------------------------------------------------------
# Collection Pipeline Endpoints
# -------------------------------------------------------------------------

api_router.include_router(
    collection_router,
    prefix="/api/v1/collection",
    tags=["Collection"],
)

# -------------------------------------------------------------------------
# Server Management Endpoints
# -------------------------------------------------------------------------

api_router.include_router(
    servers_router,
    prefix="/api/v1/servers",
    tags=["Servers"],
)

# -------------------------------------------------------------------------
# Dashboard Endpoints
# -------------------------------------------------------------------------

api_router.include_router(
    dashboard_router,
    prefix="/api/v1/dashboard",
    tags=["Dashboard"],
)

# -------------------------------------------------------------------------
# Admin Endpoints
# -------------------------------------------------------------------------

api_router.include_router(
    admin_router,
    prefix="/api/v1/admin",
    tags=["Admin"],
)

# -------------------------------------------------------------------------
# Alerts Endpoints
# -------------------------------------------------------------------------

api_router.include_router(
    alerts_router,
    prefix="/api/v1/alerts",
    tags=["Alerts"],
)

# -------------------------------------------------------------------------
# Detection Endpoints
# -------------------------------------------------------------------------

api_router.include_router(
    detection_router,
    prefix="/api/v1/detection",
    tags=["Detection"],
)

__all__ = ["api_router"]