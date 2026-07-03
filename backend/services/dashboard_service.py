"""Business logic service layer for dashboard intelligence and telemetry analytics."""
from __future__ import annotations

import logging
from sqlalchemy.orm import Session

from backend.database import crud

logger = logging.getLogger(__name__)


class DashboardService:
    """Service layer providing aggregated security telemetry and metrics for dashboards."""

    def __init__(self, session: Session) -> None:
        """Initialize the dashboard service with a database session."""
        self._session = session

    def dashboard_summary(self) -> dict[str, int]:
        """Calculate and return overall SIEM summary statistics across collected security logs."""
        logger.debug("Generating comprehensive dashboard summary metrics")
        return crud.dashboard_summary(self._session)

    def count_events(self) -> int:
        """Return the total number of recorded security events."""
        logger.debug("Counting total security events")
        return crud.count_events(self._session)

    def count_high_risk_events(self, min_score: int = 70) -> int:
        """Return the number of high-risk events meeting or exceeding the threshold."""
        logger.debug("Counting high-risk events with min_score=%d", min_score)
        return crud.count_high_risk_events(self._session, min_score=min_score)

    def count_successful_logins(self) -> int:
        """Return the number of successful authentication events."""
        logger.debug("Counting successful login events")
        return crud.count_successful_logins(self._session)

    def count_failed_logins(self) -> int:
        """Return the number of failed authentication events."""
        logger.debug("Counting failed login events")
        return crud.count_failed_logins(self._session)