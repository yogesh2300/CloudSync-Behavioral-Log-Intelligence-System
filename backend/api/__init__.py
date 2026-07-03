"""API layer package initialization and router aggregation for CloudSync."""
from __future__ import annotations

from typing import Iterator

from fastapi import APIRouter
from sqlalchemy.orm import Session

from backend.api.dashboard import router as dashboard_router
from backend.api.events import router as events_router
from backend.api.health import router as health_router
from backend.database.connection import get_session


def get_db() -> Iterator[Session]:
    """Yield a database session for FastAPI request dependency injection."""
    session = get_session()
    try:
        yield session
    finally:
        session.close()


api_router = APIRouter()
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(events_router, prefix="/api/v1/events", tags=["Events"])
api_router.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard"])

__all__ = ["api_router", "get_db"]