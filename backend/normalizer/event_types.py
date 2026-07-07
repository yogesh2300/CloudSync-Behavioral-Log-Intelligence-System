"""Security event type definitions for the DefenSync normalizer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class EventCategory(StrEnum):
    """High-level grouping for normalized security events."""

    AUTHENTICATION = "authentication"
    IDENTITY = "identity"
    PRIVILEGE = "privilege"
    FILE_SYSTEM = "file_system"
    PROCESS = "process"


class EventType(StrEnum):
    """Supported normalized security event types."""

    FAILED_LOGIN = "Failed Login"
    SUCCESSFUL_LOGIN = "Successful Login"
    USER_CREATION = "User Creation"
    USER_DELETION = "User Deletion"
    SUDO_COMMAND = "Sudo Command"
    FILE_MODIFICATION = "File Modification"
    DIRECTORY_CREATION = "Directory Creation"
    PERMISSION_CHANGE = "Permission Change"
    COMMAND_EXECUTION = "Command Execution"


EVENT_CATEGORY_MAP: dict[EventType, EventCategory] = {
    EventType.FAILED_LOGIN: EventCategory.AUTHENTICATION,
    EventType.SUCCESSFUL_LOGIN: EventCategory.AUTHENTICATION,
    EventType.USER_CREATION: EventCategory.IDENTITY,
    EventType.USER_DELETION: EventCategory.IDENTITY,
    EventType.SUDO_COMMAND: EventCategory.PRIVILEGE,
    EventType.FILE_MODIFICATION: EventCategory.FILE_SYSTEM,
    EventType.DIRECTORY_CREATION: EventCategory.FILE_SYSTEM,
    EventType.PERMISSION_CHANGE: EventCategory.FILE_SYSTEM,
    EventType.COMMAND_EXECUTION: EventCategory.PROCESS,
}


def category_for(event_type: EventType) -> EventCategory:
    """Return the category associated with an event type."""
    return EVENT_CATEGORY_MAP[event_type]


@dataclass(frozen=True, slots=True)
class NormalizedSecurityEvent:
    """Standardized security event emitted by the normalizer."""

    event_id: str
    timestamp: str
    hostname: str
    username: str | None
    source_ip: str | None
    event_type: EventType
    category: EventCategory
    severity: str
    risk_score: int
    raw_log: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the event to a JSON-compatible dictionary."""
        payload = asdict(self)
        payload["event_type"] = self.event_type.value
        payload["category"] = self.category.value
        return payload

    def to_persistence_dict(self) -> dict[str, Any]:
        """Map to a payload compatible with SecurityEvent ingestion and CRUD."""
        metadata = dict(self.metadata)
        message = metadata.get("message") or self.raw_log or self.event_type.value
        process = metadata.get("process")
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "hostname": self.hostname,
            "username": self.username,
            "source_ip": self.source_ip,
            "event_type": self.event_type.value,
            "category": self.category.value,
            "severity": self.severity,
            "risk_score": self.risk_score,
            "message": message,
            "raw_log": self.raw_log,
            "process": process,
            "metadata": metadata,
        }
