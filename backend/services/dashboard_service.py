"""Business logic service for dashboard intelligence and analytics."""
from __future__ import annotations

import logging
from sqlalchemy.orm import Session

from backend.database import crud

logger = logging.getLogger(__name__)


class DashboardService:
    """Service layer providing aggregated security intelligence for dashboards."""

    def __init__(self, session: Session) -> None:
        """Initialize the dashboard service with a database session."""
        self._session = session

    def get_summary_metrics(self) -> dict[str, int]:
        """Calculate summary statistics across all collected security logs."""
        logger.debug("Generating dashboard summary metrics")
        return crud.dashboard_summary(self._session)