"""Behavioral log parser for DefenSync secure.log and audit.log entries."""

from backend.parser.audit_events import parse_audit_event
from backend.parser.engine import (
    parse_audit_line,
    parse_logs,
    parse_secure_line,
    summarize_events,
)
from backend.parser.event_types import EventType
from backend.parser.schemas import ParsedEvent, build_event
from backend.parser.secure_events import parse_secure_event

__all__ = [
    "EventType",
    "ParsedEvent",
    "build_event",
    "parse_audit_event",
    "parse_audit_line",
    "parse_logs",
    "parse_secure_event",
    "parse_secure_line",
    "summarize_events",
]
