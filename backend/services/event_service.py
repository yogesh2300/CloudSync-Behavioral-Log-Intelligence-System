"""Business logic service layer for security event querying and persistence."""
from __future__ import annotations

import logging
from typing import Any, Iterable, Mapping
from sqlalchemy.orm import Session

from backend.database import crud
from backend.database.models import SecurityEvent
from backend.core.exceptions import DatabaseException

logger = logging.getLogger(__name__)


class EventService:
    """Service layer coordinating business logic and database CRUD operations for security events."""

    def __init__(self, session: Session) -> None:
        """Initialize the event service with a database session."""
        self._session = session

    def get_recent_events(self, limit: int = 100) -> list[SecurityEvent]:
        """Retrieve recent security events ordered by timestamp."""
        logger.debug("Retrieving recent events with limit=%d", limit)
        return crud.get_recent_events(self._session, limit=limit)

    def get_event_by_id(self, event_id: str) -> SecurityEvent | None:
        """Retrieve a specific security event by its unique UUID string."""
        logger.debug("Retrieving event by ID: %s", event_id)
        return crud.get_event_by_id(self._session, event_id)

    def get_events_by_username(self, username: str, limit: int = 100) -> list[SecurityEvent]:
        """Retrieve security events associated with a specific username."""
        logger.debug("Retrieving events for username=%s with limit=%d", username, limit)
        return crud.get_events_by_username(self._session, username, limit=limit)

    def get_events_by_ip(self, ip: str, limit: int = 100) -> list[SecurityEvent]:
        """Retrieve security events originating from a specific source IP address."""
        logger.debug("Retrieving events for source_ip=%s with limit=%d", ip, limit)
        return crud.get_events_by_ip(self._session, ip, limit=limit)

    def get_events_by_type(self, event_type: str, limit: int = 100) -> list[SecurityEvent]:
        """Retrieve security events matching a specific event type."""
        logger.debug("Retrieving events for event_type=%s with limit=%d", event_type, limit)
        return crud.get_events_by_type(self._session, event_type, limit=limit)

    def get_high_risk_events(self, min_score: int = 70, limit: int = 100) -> list[SecurityEvent]:
        """Retrieve security events meeting or exceeding the minimum risk score threshold."""
        logger.debug("Retrieving high-risk events with min_score=%d and limit=%d", min_score, limit)
        return crud.get_high_risk_events(self._session, min_score=min_score, limit=limit)

    def insert_event(self, event: Mapping[str, Any]) -> SecurityEvent:
        """Persist a single normalized security event dictionary into the database."""
        logger.info("Persisting new security event: %s", event.get("event_type", "Unknown"))
        return crud.insert_event(self._session, event)

    def insert_many(self, events: Iterable[Mapping[str, Any]]) -> list[SecurityEvent]:
        """Persist multiple normalized security events into the database."""
        event_list = list(events)
        logger.info("Persisting batch of %d security events", len(event_list))
        return crud.insert_many(self._session, event_list)
    
    
    def ingest_single_event(
        self,
        event: Mapping[str, Any],
    ) -> SecurityEvent:
        """Persist a single security event using a transaction."""
        
        logger.info(
            "Ingesting security event: %s",
            event.get("event_id"),
        )
        
        try:
            record = crud.insert_event(
                self._session,
                event,
            )
            
            self._session.commit()
            
            logger.info("Security event stored successfully.)
            
            return record
        
        except Exception as exc:
            self._session.rollback()

            logger.exception(
                "Failed to ingest security event."
            )

            raise DatabaseException(
                "Failed to store security event."
            ) from exc