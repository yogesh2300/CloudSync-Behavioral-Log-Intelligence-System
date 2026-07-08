"""Background health monitoring engine — periodic and on-demand checks without blocking APIs."""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any

from backend.core.config import get_settings
from backend.core.logging import get_logger
from backend.services.health_service import HealthService

logger = get_logger(__name__)


class HealthEngine:
    """Coordinates non-blocking, concurrent server health check cycles."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._running = False
        self._last_run_at: datetime | None = None
        self._last_run_stats: dict[str, Any] = {}

    @property
    def last_run_at(self) -> datetime | None:
        return self._last_run_at

    @property
    def last_run_stats(self) -> dict[str, Any]:
        return dict(self._last_run_stats)

    @property
    def is_running(self) -> bool:
        return self._running

    def trigger_async(
        self,
        *,
        owner_id: str | None = None,
        server_id: str | None = None,
    ) -> dict[str, Any]:
        """Queue a health check cycle without blocking the caller."""
        if self._running:
            return {
                "accepted": False,
                "status": "running",
                "message": "Health check cycle already in progress.",
                "last_run_at": self._last_run_at.isoformat() if self._last_run_at else None,
            }

        thread = threading.Thread(
            target=self._run_cycle_safe,
            kwargs={"owner_id": owner_id, "server_id": server_id},
            name="health-engine-async",
            daemon=True,
        )
        thread.start()
        return {
            "accepted": True,
            "status": "queued",
            "message": "Health check cycle started.",
        }

    def run_cycle(
        self,
        *,
        owner_id: str | None = None,
        server_id: str | None = None,
    ) -> dict[str, Any]:
        """Run a health check cycle synchronously (scheduler/worker use)."""
        return self._run_cycle_safe(owner_id=owner_id, server_id=server_id)

    def _run_cycle_safe(
        self,
        *,
        owner_id: str | None = None,
        server_id: str | None = None,
    ) -> dict[str, Any]:
        settings = get_settings()
        if not settings.HEALTH_CHECK_ENABLED:
            return {"skipped": True, "reason": "health_checks_disabled"}

        with self._lock:
            if self._running:
                return {"skipped": True, "reason": "already_running"}
            self._running = True

        try:
            stats = HealthService().check_all_servers(owner_id=owner_id, server_id=server_id)
            self._last_run_at = datetime.now(timezone.utc)
            self._last_run_stats = stats
            return stats
        except Exception:
            logger.exception("Health engine cycle failed")
            return {"skipped": True, "reason": "cycle_failed"}
        finally:
            with self._lock:
                self._running = False


_engine: HealthEngine | None = None


def get_health_engine() -> HealthEngine:
    global _engine
    if _engine is None:
        _engine = HealthEngine()
    return _engine


def start_health_engine() -> None:
    """Start periodic health monitoring and run an initial async cycle."""
    settings = get_settings()
    if not settings.HEALTH_CHECK_ENABLED:
        logger.info("Server health engine disabled (HEALTH_CHECK_ENABLED=false).")
        return

    engine = get_health_engine()
    engine.trigger_async()
    logger.info(
        "Server health engine started interval=%ss workers=%s timeout=%ss",
        settings.HEALTH_CHECK_INTERVAL_SECONDS,
        settings.HEALTH_CHECK_MAX_WORKERS,
        settings.HEALTH_CHECK_TIMEOUT_SECONDS,
    )


def stop_health_engine() -> None:
    """Placeholder for graceful shutdown hooks."""
    logger.info("Server health engine stopped.")
