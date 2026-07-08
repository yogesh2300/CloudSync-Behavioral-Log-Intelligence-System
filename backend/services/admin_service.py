"""Global platform analytics for the Admin Dashboard."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import case, desc, func, select
from sqlalchemy.orm import Session

from backend.database import crud, server_crud
from backend.database.models import Alert, CollectionRun, Detection, Event, Server, User
from backend.services.alert_service import AlertService
from backend.services.analytics_service import AnalyticsService
from backend.services.dashboard_service import DashboardService
from backend.services.detection_service import DetectionService
from backend.services.server_service import ServerService

logger = logging.getLogger(__name__)


def _hour_label(value: datetime | None) -> str:
    if not value:
        return ""
    return value.strftime("%H:00")


def _day_label(value: datetime | None) -> str:
    if not value:
        return ""
    return value.strftime("%Y-%m-%d")


class AdminService:
    """Aggregated cross-tenant metrics — admin only (no owner_id filter)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def dashboard(self) -> dict[str, Any]:
        summary = DashboardService(self._session).dashboard_summary(owner_id=None)
        health = server_crud.health_summary(self._session)
        alert_row = self._session.execute(
            select(
                func.count(Alert.id),
                func.sum(case((Alert.acknowledged.is_(False), 1), else_=0)),
                func.sum(case((Alert.severity == "critical", 1), else_=0)),
            )
        ).one()
        detection_count = self._session.scalar(select(func.count(Detection.id))) or 0
        ml_anomalies = self._session.scalar(
            select(func.count(Detection.id)).where(Detection.is_anomaly.is_(True))
        ) or 0
        collection_runs = self._session.scalar(select(func.count(CollectionRun.id))) or 0
        successful_runs = self._session.scalar(
            select(func.count(CollectionRun.id)).where(CollectionRun.status == "completed")
        ) or 0
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_collections = self._session.scalar(
            select(func.count(CollectionRun.id)).where(CollectionRun.started_at >= today_start)
        ) or 0
        events_today = self._session.scalar(
            select(func.count(Event.id)).where(Event.timestamp >= today_start)
        ) or 0
        total_users = self._session.scalar(select(func.count(User.id))) or 0
        active_users = self._session.scalar(
            select(func.count(func.distinct(Event.owner_id))).where(Event.owner_id.is_not(None))
        ) or 0
        total = health["total_servers"]
        online = health["online_servers"]
        availability = round((online / total) * 100) if total else 0
        success_rate = round((successful_runs / collection_runs) * 100) if collection_runs else 0

        return {
            **summary,
            **health,
            "total_users": total_users,
            "active_users": int(active_users),
            "availability_pct": availability,
            "events_today": int(events_today),
            "total_alerts": int(alert_row[0] or 0),
            "open_alerts": int(alert_row[1] or 0),
            "critical_alerts": int(alert_row[2] or 0),
            "total_detections": detection_count,
            "ml_anomalies": int(ml_anomalies),
            "ml_predictions": detection_count,
            "collection_runs": collection_runs,
            "collection_success_rate": success_rate,
            "todays_collections": today_collections,
            "average_risk_score": int(round(summary.get("average_risk_score") or 0)),
        }

    def charts(self) -> dict[str, Any]:
        analytics = AnalyticsService(self._session).get_event_stats(owner_id=None)
        now = datetime.now(timezone.utc)

        day_col = func.date_trunc("day", User.created_at).label("day")
        user_trend = self._session.execute(
            select(day_col, func.count(User.id))
            .where(User.created_at >= now - timedelta(days=30))
            .group_by(day_col)
            .order_by(day_col)
        ).all()
        user_registration_trend = [{"day": _day_label(row[0]), "count": int(row[1])} for row in user_trend]

        server_by_owner = self._session.execute(
            select(Server.owner_id, func.count(Server.id))
            .group_by(Server.owner_id)
            .order_by(desc(func.count(Server.id)))
            .limit(10)
        ).all()
        server_distribution = [
            {"owner_id": row[0] or "unassigned", "count": int(row[1])}
            for row in server_by_owner
        ]

        os_rows = self._session.execute(
            select(Server.operating_system, func.count(Server.id))
            .group_by(Server.operating_system)
            .order_by(desc(func.count(Server.id)))
        ).all()
        linux_distribution = [{"os": row[0] or "unknown", "count": int(row[1])} for row in os_rows]

        top_users = self._session.execute(
            select(Event.username, func.count(Event.id))
            .where(Event.username.is_not(None), Event.username != "")
            .group_by(Event.username)
            .order_by(desc(func.count(Event.id)))
            .limit(10)
        ).all()
        top_active_users = [{"username": r[0], "count": int(r[1])} for r in top_users]

        top_servers = self._session.execute(
            select(Server.server_name, func.count(Event.id))
            .join(Event, Event.server_id == Server.id, isouter=True)
            .group_by(Server.id, Server.server_name)
            .order_by(desc(func.count(Event.id)))
            .limit(10)
        ).all()
        most_active_servers = [{"server": r[0], "events": int(r[1])} for r in top_servers]

        hour_col = func.date_trunc("hour", CollectionRun.started_at).label("hour")
        collections_hourly = self._session.execute(
            select(hour_col, func.count(CollectionRun.id))
            .where(CollectionRun.started_at >= now - timedelta(hours=24))
            .group_by(hour_col)
            .order_by(hour_col)
        ).all()
        collections_per_hour = [{"hour": _hour_label(r[0]), "count": int(r[1])} for r in collections_hourly]

        risk_band = case(
            (Event.risk_score >= 70, "high"),
            (Event.risk_score >= 40, "medium"),
            else_="low",
        ).label("band")
        risk_rows = self._session.execute(
            select(risk_band, func.count(Event.id)).group_by(risk_band)
        ).all()
        risk_distribution = {row[0]: int(row[1]) for row in risk_rows}

        resource = self._session.execute(
            select(
                func.avg(Event.cpu_usage),
                func.avg(Event.memory_usage),
                func.avg(Event.disk_usage),
                func.avg(Event.network_connections),
            )
        ).one()

        alert_sev_rows = self._session.execute(
            select(Alert.severity, func.count(Alert.id)).group_by(Alert.severity)
        ).all()
        alert_severity = {row[0]: int(row[1]) for row in alert_sev_rows}

        events_day_col = func.date_trunc("day", Event.timestamp).label("day")
        events_by_day_rows = self._session.execute(
            select(events_day_col, func.count(Event.id))
            .where(Event.timestamp >= now - timedelta(days=30))
            .group_by(events_day_col)
            .order_by(events_day_col)
        ).all()
        events_by_day = [{"day": _day_label(r[0]), "count": int(r[1])} for r in events_by_day_rows]

        alerts_day_col = func.date_trunc("day", Alert.created_at).label("day")
        alerts_trend_rows = self._session.execute(
            select(alerts_day_col, func.count(Alert.id))
            .where(Alert.created_at >= now - timedelta(days=30))
            .group_by(alerts_day_col)
            .order_by(alerts_day_col)
        ).all()
        alerts_trend = [{"day": _day_label(r[0]), "count": int(r[1])} for r in alerts_trend_rows]

        return {
            "user_registration_trend": user_registration_trend,
            "server_distribution": server_distribution,
            "linux_distribution": linux_distribution,
            "event_timeline": analytics.get("hourly_trends") or [],
            "events_by_day": events_by_day,
            "events_by_severity": analytics.get("by_severity") or {},
            "events_by_type": analytics.get("by_event_type") or {},
            "detection_timeline": self._detection_timeline(),
            "alert_severity": alert_severity,
            "alerts_trend": alerts_trend,
            "top_active_users": top_active_users,
            "most_active_servers": most_active_servers,
            "collections_per_hour": collections_per_hour,
            "risk_distribution": risk_distribution,
            "cpu_usage_avg": round(float(resource[0] or 0), 1),
            "memory_usage_avg": round(float(resource[1] or 0), 1),
            "disk_usage_avg": round(float(resource[2] or 0), 1),
            "network_activity_avg": round(float(resource[3] or 0), 1),
        }

    def analytics(self) -> dict[str, Any]:
        charts = self.charts()
        top_alerts = self._session.execute(
            select(Alert.title, func.count(Alert.id))
            .group_by(Alert.title)
            .order_by(desc(func.count(Alert.id)))
            .limit(10)
        ).all()
        top_events = self._session.execute(
            select(Event.event_type, func.count(Event.id))
            .group_by(Event.event_type)
            .order_by(desc(func.count(Event.id)))
            .limit(10)
        ).all()

        top_risk_servers = self._session.execute(
            select(Server.server_name, func.avg(Event.risk_score), func.count(Event.id))
            .join(Event, Event.server_id == Server.id)
            .group_by(Server.id, Server.server_name)
            .order_by(desc(func.avg(Event.risk_score)))
            .limit(10)
        ).all()
        top_risk_users = self._session.execute(
            select(Event.username, func.avg(Event.risk_score), func.count(Event.id))
            .where(Event.username.is_not(None), Event.username != "")
            .group_by(Event.username)
            .order_by(desc(func.avg(Event.risk_score)))
            .limit(10)
        ).all()

        detection_dist_rows = self._session.execute(
            select(Detection.classification, func.count(Detection.id))
            .group_by(Detection.classification)
        ).all()
        detection_distribution = {
            (row[0] or "unknown"): int(row[1]) for row in detection_dist_rows
        }

        user_activity = [
            {"username": row[0], "events": int(row[2]), "avg_risk": int(round(row[1] or 0))}
            for row in top_risk_users
        ]

        health = server_crud.health_summary(self._session)
        total = health["total_servers"]
        online = health["online_servers"]
        server_availability_trend = [{
            "label": "current",
            "availability_pct": round((online / total) * 100) if total else 0,
            "online": online,
            "offline": health["offline_servers"],
        }]

        return {
            **charts,
            "top_users": charts["top_active_users"],
            "top_servers": charts["most_active_servers"],
            "top_risk_servers": [
                {"server": r[0], "avg_risk": int(round(r[1] or 0)), "events": int(r[2])}
                for r in top_risk_servers
            ],
            "top_risk_users": user_activity,
            "user_activity": user_activity,
            "detection_distribution": detection_distribution,
            "server_availability_trend": server_availability_trend,
            "most_frequent_alerts": [{"title": r[0], "count": int(r[1])} for r in top_alerts],
            "most_common_events": [{"event_type": r[0], "count": int(r[1])} for r in top_events],
        }

    def list_users_enriched(
        self,
        *,
        search: str | None = None,
        limit: int = 500,
        offset: int = 0,
    ) -> dict[str, Any]:
        users = crud.list_users(self._session)
        if search:
            term = search.strip().lower()
            users = [
                user for user in users
                if term in user.username.lower()
                or term in user.email.lower()
                or term in user.role.lower()
            ]
        total = len(users)
        users = users[offset: offset + limit]
        result: list[dict[str, Any]] = []
        for user in users:
            servers = self._session.scalar(
                select(func.count(Server.id)).where(
                    (Server.owner_id == user.id) | (Server.created_by == user.id)
                )
            ) or 0
            events = self._session.scalar(
                select(func.count(Event.id)).where(Event.owner_id == user.id)
            ) or 0
            result.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at,
                "servers": int(servers),
                "events": int(events),
                "alerts": int(
                    self._session.scalar(
                        select(func.count(Alert.id)).where(Alert.owner_id == user.id)
                    ) or 0
                ),
                "detections": int(
                    self._session.scalar(
                        select(func.count(Detection.id)).where(Detection.owner_id == user.id)
                    ) or 0
                ),
                "last_login": None,
                "status": "active",
            })
        return {"items": result, "total": total, "limit": limit, "offset": offset}

    def user_detail(self, user_id: str) -> dict[str, Any]:
        user = self._session.get(User, user_id)
        if user is None:
            raise ValueError(f"User '{user_id}' not found.")
        servers = list(
            self._session.scalars(
                select(Server).where(
                    (Server.owner_id == user_id) | (Server.created_by == user_id)
                )
            ).all()
        )
        events_count = self._session.scalar(
            select(func.count(Event.id)).where(Event.owner_id == user_id)
        ) or 0
        alerts_count = self._session.scalar(
            select(func.count(Alert.id)).where(Alert.owner_id == user_id)
        ) or 0
        detections_count = self._session.scalar(
            select(func.count(Detection.id)).where(Detection.owner_id == user_id)
        ) or 0
        avg_risk = self._session.scalar(
            select(func.avg(Event.risk_score)).where(Event.owner_id == user_id)
        )
        recent_events = list(
            self._session.scalars(
                select(Event)
                .where(Event.owner_id == user_id)
                .order_by(desc(Event.timestamp))
                .limit(20)
            ).all()
        )
        collections = list(
            self._session.scalars(
                select(CollectionRun)
                .join(Server, CollectionRun.server_id == Server.id)
                .where((Server.owner_id == user_id) | (Server.created_by == user_id))
                .order_by(desc(CollectionRun.started_at))
                .limit(20)
            ).all()
        )
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at,
            "servers": [
                {
                    "id": s.id,
                    "server_name": s.server_name,
                    "host": s.host,
                    "health_status": s.health_status,
                    "status": s.status,
                }
                for s in servers
            ],
            "events_count": int(events_count),
            "alerts_count": int(alerts_count),
            "detections_count": int(detections_count),
            "average_risk_score": int(round(avg_risk or 0)),
            "recent_events": [
                {
                    "event_id": e.event_id,
                    "event_type": e.event_type,
                    "severity": e.severity,
                    "risk_score": e.risk_score,
                    "timestamp": e.timestamp,
                    "message": e.message[:120] if e.message else "",
                }
                for e in recent_events
            ],
            "collection_history": [
                {
                    "id": c.id,
                    "server_id": c.server_id,
                    "status": c.status,
                    "inserted": c.inserted,
                    "started_at": c.started_at,
                    "duration_ms": c.duration_ms,
                }
                for c in collections
            ],
        }

    def list_servers_enriched(self) -> list[dict[str, Any]]:
        servers = ServerService(self._session).list_server_rows(owner_id=None)
        users = {user.id: user.username for user in crud.list_users(self._session)}
        enriched: list[dict[str, Any]] = []
        for server in servers:
            events_count = self._session.scalar(
                select(func.count(Event.id)).where(Event.server_id == server["id"])
            ) or 0
            owner_id = server.get("owner_id")
            enriched.append({
                **server,
                "owner_username": users.get(owner_id, "—") if owner_id else "—",
                "events_count": int(events_count),
            })
        return enriched

    def list_alerts_enriched(
        self,
        *,
        limit: int = 500,
        acknowledged: bool | None = None,
    ) -> list[dict[str, Any]]:
        alerts = AlertService(self._session).list_alerts(
            limit=limit,
            acknowledged=acknowledged,
            owner_id=None,
        )
        users = {user.id: user.username for user in crud.list_users(self._session)}
        servers = {
            row.id: row.server_name
            for row in self._session.scalars(select(Server)).all()
        }
        return [
            {
                "id": alert.id,
                "event_id": alert.event_id,
                "server_id": alert.server_id,
                "server_name": servers.get(alert.server_id, "—"),
                "owner_id": alert.owner_id,
                "owner_username": users.get(alert.owner_id, "—") if alert.owner_id else "—",
                "title": alert.title,
                "message": alert.message,
                "severity": alert.severity,
                "risk_score": alert.risk_score,
                "detection_type": alert.detection_type,
                "acknowledged": alert.acknowledged,
                "status": "resolved" if alert.acknowledged else "open",
                "created_at": alert.created_at,
            }
            for alert in alerts
        ]

    def list_detections(self, *, limit: int = 100) -> list[dict[str, Any]]:
        rows = self._session.execute(
            select(Detection, Event, Server)
            .join(Event, Event.event_id == Detection.event_id, isouter=True)
            .join(Server, Server.id == Detection.server_id, isouter=True)
            .order_by(desc(Detection.created_at))
            .limit(limit)
        ).all()
        users = {user.id: user.username for user in crud.list_users(self._session)}
        items: list[dict[str, Any]] = []
        for detection, event, server in rows:
            owner_id = detection.owner_id or (server.owner_id if server else None)
            model = detection.detection_type
            if not model:
                if detection.isolation_score is not None:
                    model = "Isolation Forest"
                elif detection.random_forest_label:
                    model = "Random Forest"
                else:
                    model = "Rule Engine"
            items.append({
                "id": detection.id,
                "event_id": detection.event_id,
                "prediction": detection.classification or detection.random_forest_label or (
                    "Anomaly" if detection.is_anomaly else "Normal"
                ),
                "confidence": detection.confidence,
                "model": model,
                "risk_score": detection.risk_score,
                "timestamp": detection.created_at,
                "server_id": detection.server_id,
                "server_name": server.server_name if server else None,
                "owner_id": owner_id,
                "owner_username": users.get(owner_id) if owner_id else None,
                "username": event.username if event else None,
                "event_type": event.event_type if event else None,
                "severity": event.severity if event else None,
                "isolation_score": detection.isolation_score,
                "random_forest_label": detection.random_forest_label,
                "is_anomaly": detection.is_anomaly,
                "anomaly_score": detection.isolation_score,
                "classification": detection.classification,
                "detection_type": detection.detection_type,
                "message": detection.message or (event.message if event else None),
            })
        return items

    def detection_summary(self) -> dict[str, Any]:
        total = self._session.scalar(select(func.count(Detection.id))) or 0
        anomalies = self._session.scalar(
            select(func.count(Detection.id)).where(Detection.is_anomaly.is_(True))
        ) or 0
        status = DetectionService(self._session).status(owner_id=None)
        return {
            **status,
            "total_detections": total,
            "ml_anomalies": int(anomalies),
            "events_analyzed": status.get("events_in_db", 0),
        }

    def system_health(self) -> dict[str, Any]:
        health = server_crud.health_summary(self._session)
        resource = self._session.execute(
            select(
                func.avg(Event.cpu_usage),
                func.avg(Event.memory_usage),
                func.avg(Event.disk_usage),
                func.avg(Event.network_connections),
            )
        ).one()
        try:
            self._session.execute(select(func.count(User.id)))
            database = "connected"
        except Exception:
            database = "disconnected"

        from backend.core.config import get_settings
        settings = get_settings()

        return {
            "database": database,
            "backend": "healthy",
            "api": "healthy",
            "frontend": "healthy",
            "ssh_collector": "healthy",
            "collection_engine": "running" if settings.SCHEDULER_ENABLED else "idle",
            "ml_engine": "ready" if (self._session.scalar(select(func.count(Event.id))) or 0) >= 10 else "idle",
            "connected_servers": health["online_servers"],
            "offline_servers": health["offline_servers"],
            "average_ssh_latency_ms": health.get("average_ssh_latency_ms", 0),
            "cpu_usage_avg": round(float(resource[0] or 0), 1),
            "memory_usage_avg": round(float(resource[1] or 0), 1),
            "disk_usage_avg": round(float(resource[2] or 0), 1),
            "network_activity_avg": round(float(resource[3] or 0), 1),
        }

    def ml_stats(self) -> dict[str, Any]:
        total = self._session.scalar(select(func.count(Detection.id))) or 0
        anomalies = self._session.scalar(
            select(func.count(Detection.id)).where(Detection.is_anomaly.is_(True))
        ) or 0
        avg_risk = self._session.scalar(select(func.avg(Detection.risk_score))) or 0
        iso_count = self._session.scalar(
            select(func.count(Detection.id)).where(Detection.isolation_score.is_not(None))
        ) or 0
        rf_count = self._session.scalar(
            select(func.count(Detection.id)).where(Detection.random_forest_label.is_not(None))
        ) or 0
        last = self._session.scalar(select(func.max(Detection.created_at)))
        training_size = self._session.scalar(select(func.count(Event.id))) or 0
        status = DetectionService(self._session).status(owner_id=None)
        return {
            "training_dataset_size": training_size,
            "isolation_forest_status": "active" if iso_count else "idle",
            "random_forest_status": "active" if rf_count else "idle",
            "last_training_time": last.isoformat() if last else None,
            "total_predictions": total,
            "anomaly_count": anomalies,
            "average_risk_score": int(round(avg_risk)),
            "detection_status": status,
        }

    def list_collections(self, *, limit: int = 100) -> list[dict[str, Any]]:
        runs = list(
            self._session.scalars(
                select(CollectionRun).order_by(desc(CollectionRun.started_at)).limit(limit)
            ).all()
        )
        users = {user.id: user.username for user in crud.list_users(self._session)}
        result = []
        for run in runs:
            server = self._session.get(Server, run.server_id)
            owner_id = (server.owner_id or server.created_by) if server else None
            result.append({
                "id": run.id,
                "server_id": run.server_id,
                "server_name": server.server_name if server else "unknown",
                "owner_id": owner_id,
                "owner_username": users.get(owner_id, "—") if owner_id else "—",
                "status": run.status,
                "inserted": run.inserted,
                "processed": run.processed,
                "failed": run.failed,
                "events_collected": run.inserted,
                "errors": run.failed,
                "duration_ms": run.duration_ms,
                "started_at": run.started_at,
                "completed_at": run.completed_at,
                "error_message": run.error_message,
            })
        return result

    def _detection_timeline(self) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        hour_col = func.date_trunc("hour", Detection.created_at).label("hour")
        rows = self._session.execute(
            select(hour_col, func.count(Detection.id))
            .where(Detection.created_at >= now - timedelta(hours=24))
            .group_by(hour_col)
            .order_by(hour_col)
        ).all()
        return [{"hour": _hour_label(r[0]), "count": int(r[1])} for r in rows]
