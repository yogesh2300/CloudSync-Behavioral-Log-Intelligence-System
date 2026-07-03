"""Business logic service for security events."""
from __future__ import annotations

import logging
from sqlalchemy.orm import Session

from backend.database import crud
from backend.database.models import SecurityEvent

logger = logging.getLogger(__name__)


class EventService:
    """Service layer for querying and managing security events."""

    def __init__(self, session: Session) -> None:
        """Initialize the event service with a database session."""
        self._session = session

    def list_recent_events(self, limit: int = 100) -> list[SecurityEvent]:
        """Retrieve recent security events up to the specified limit."""
        logger.debug("Fetching recent security events with limit=%d", limit)
        return crud.get_recent_events(self._session, limit=limit)

    def list_high_risk_events(self, min_score: int = 70, limit: int = 100) -> list[SecurityEvent]:
        """Retrieve high-risk security events meeting or exceeding min_score."""
        logger.debug("Fetching high-risk events with min_score=%d, limit=%d", min_score, limit)
        return crud.get_high_risk_events(self._session, min_score=min_score, limit=limit)

    def get_event(self, event_id: str) -> SecurityEvent | None:
        """Retrieve a specific security event by its UUID string."""
        logger.debug("Fetching security event by id: %s", event_id)
        return crud.get_event_by_id(self._session, event_id)