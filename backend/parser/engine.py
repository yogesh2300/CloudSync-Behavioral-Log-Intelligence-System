"""Main log parsing engine — dispatches lines to secure and audit classifiers."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from backend.parser.audit_events import parse_audit_event
from backend.parser.secure_events import parse_secure_event
from backend.parser.utils import parse_audit_fields


def parse_secure_line(raw_line: str, line_number: int | None = None) -> dict[str, Any] | None:
    """
    Parse a single /var/log/secure line into a structured event.

    Returns None when the line is blank, malformed, or not a supported event type.
    """
    event = parse_secure_event(raw_line)
    if event is None:
        return None
    event["source"] = "secure"
    event["raw"] = raw_line
    if line_number is not None:
        event["line_number"] = line_number
    return event


def parse_audit_line(raw_line: str, line_number: int | None = None) -> dict[str, Any] | None:
    """
    Parse a single /var/log/audit/audit.log line into a structured event.

    Returns None when the line is blank, malformed, or not a supported event type.
    """
    event = parse_audit_event(raw_line)
    if event is None:
        return None
    fields = parse_audit_fields(raw_line.strip())
    event["source"] = "audit"
    event["raw"] = raw_line
    event["type"] = fields.get("type")
    event["fields"] = fields
    if line_number is not None:
        event["line_number"] = line_number
    return event


def parse_logs(
    secure_lines: Iterable[str],
    audit_lines: Iterable[str],
) -> list[dict[str, Any]]:
    """Parse secure and audit log lines, returning only recognized security events."""
    events: list[dict[str, Any]] = []

    for index, line in enumerate(secure_lines, start=1):
        if event := parse_secure_line(line, line_number=index):
            events.append(event)

    for index, line in enumerate(audit_lines, start=1):
        if event := parse_audit_line(line, line_number=index):
            events.append(event)

    return events


def summarize_events(events: Iterable[dict[str, Any]]) -> dict[str, int]:
    """Count parsed events grouped by event_type."""
    return dict(Counter(event["event_type"] for event in events))
