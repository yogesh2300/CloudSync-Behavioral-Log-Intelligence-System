"""Health check result types."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class HealthCheckResult:
    server_id: str
    health_status: str
    latency_ms: int | None = None
    error_message: str | None = None
    checked_at: datetime | None = None
