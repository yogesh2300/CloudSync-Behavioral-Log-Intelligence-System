"""CRUD operations for CloudSync security event persistence."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.database.models import SecurityEvent


def insert_event(session: Session, event: Mapping[str, Any]) -> SecurityEvent:
    """Persist a single security event."""
    record = _to_model(event)
    session.add(record)
    session.flush()
    session.refresh(record)
    return record


def insert_many(session: Session, events: Iterable[Mapping[str, Any]]) -> list[SecurityEvent]:
    """Persist multiple security events in one transaction."""
    records = [_to_model(event) for event in events]
    if not records:
        return []

    session.add_all(records)
    session.flush()
    for record in records:
        session.refresh(record)
    return records


def get_recent_events(session: Session, *, limit: int = 100) -> list[SecurityEvent]:
    """Return the most recent events ordered by event timestamp."""
    stmt = (
        select(SecurityEvent)
        .order_by(desc(SecurityEvent.timestamp), desc(SecurityEvent.id))
        .limit(limit)
    )
    return list(session.scalars(stmt).all())


def get_high_risk_events(
    session: Session,
    *,
    min_score: int = 70,
    limit: int = 100,
) -> list[SecurityEvent]:
    """Return events at or above the configured risk score threshold."""
    stmt = (
        select(SecurityEvent)
        .where(SecurityEvent.risk_score >= min_score)
        .order_by(desc(SecurityEvent.risk_score), desc(SecurityEvent.timestamp))
        .limit(limit)
    )
    return list(session.scalars(stmt).all())


def get_events_by_username(
    session: Session,
    username: str,
    *,
    limit: int = 100,
) -> list[SecurityEvent]:
    """Return events associated with a specific username."""
    stmt = (
        select(SecurityEvent)
        .where(SecurityEvent.username == username)
        .order_by(desc(SecurityEvent.timestamp), desc(SecurityEvent.id))
        .limit(limit)
    )
    return list(session.scalars(stmt).all())


def _to_model(event: Mapping[str, Any]) -> SecurityEvent:
    """Convert an event mapping into a SecurityEvent ORM instance."""
    payload = _normalize_payload(event)
    return SecurityEvent(
        event_id=str(payload["event_id"]),
        timestamp=_parse_timestamp(payload["timestamp"]),
        hostname=str(payload["hostname"]),
        username=payload.get("username"),
        source_ip=payload.get("source_ip"),
        event_type=str(payload["event_type"]),
        category=str(payload["category"]),
        severity=str(payload["severity"]),
        risk_score=int(payload["risk_score"]),
        process=payload.get("process"),
        message=str(payload["message"]),
        raw_log=str(payload["raw_log"]),
    )


def _normalize_payload(event: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize parser or normalizer payloads into database-ready fields."""
    if hasattr(event, "to_dict"):
        payload = event.to_dict()
    else:
        payload = dict(event)

    metadata = payload.get("metadata") or {}

    return {
        "event_id": payload.get("event_id") or str(uuid.uuid4()),
        "timestamp": payload["timestamp"],
        "hostname": payload.get("hostname") or "unknown",
        "username": payload.get("username"),
        "source_ip": payload.get("source_ip"),
        "event_type": payload["event_type"],
        "category": payload.get("category") or metadata.get("category") or "unknown",
        "severity": payload.get("severity") or metadata.get("severity") or "info",
        "risk_score": payload.get("risk_score", metadata.get("risk_score", 0)),
        "process": payload.get("process") or metadata.get("process"),
        "message": payload.get("message") or metadata.get("message") or payload.get("raw_log", ""),
        "raw_log": payload.get("raw_log") or payload.get("raw") or "",
    }


def _parse_timestamp(value: str | datetime) -> datetime:
    """Parse ISO-8601 or datetime values into timezone-aware datetimes."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    normalized = str(value).replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed
