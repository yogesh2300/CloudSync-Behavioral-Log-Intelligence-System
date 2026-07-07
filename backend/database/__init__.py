"""PostgreSQL storage layer for DefenSync behavioral log intelligence."""

from backend.database.connection import get_database_url, get_engine, get_session, session_scope
from backend.database.crud import (
    get_events_by_username,
    get_high_risk_events,
    get_recent_events,
    insert_event,
    insert_many,
)
from backend.database.init_db import create_tables
from backend.database.models import Base, Detection, Event, MLPrediction, SecurityEvent

__all__ = [
    "Base",
    "Detection",
    "Event",
    "MLPrediction",
    "SecurityEvent",
    "create_tables",
    "get_database_url",
    "get_engine",
    "get_events_by_username",
    "get_high_risk_events",
    "get_recent_events",
    "get_session",
    "insert_event",
    "insert_many",
    "session_scope",
]
