"""Structured event schema helpers for parsed log entries."""

from __future__ import annotations

from typing import Any, TypedDict


class ParsedEvent(TypedDict):
    """Structured security event extracted from a log line."""

    timestamp: str | None
    hostname: str | None
    event_type: str
    username: str | None
    source_ip: str | None
    process: str | None
    message: str
    raw_log: str


def build_event(
    *,
    event_type: str,
    message: str,
    raw_log: str,
    timestamp: str | None = None,
    hostname: str | None = None,
    username: str | None = None,
    source_ip: str | None = None,
    process: str | None = None,
) -> dict[str, Any]:
    """Build a normalized parsed-event dictionary."""
    return {
        "timestamp": timestamp,
        "hostname": hostname,
        "event_type": str(event_type),
        "username": username,
        "source_ip": source_ip,
        "process": process,
        "message": message,
        "raw_log": raw_log,
    }
