"""End-to-end event processing pipeline orchestration."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.collector.config import SSHConfig
from backend.core.logging import get_logger
from backend.normalizer.event_types import EventType, NormalizedSecurityEvent, category_for
from backend.services.collector_service import CollectorService
from backend.services.ingestion_service import IngestionService
from backend.services.transform_service import TransformService

logger = get_logger(__name__)


class PipelineService:
    """
    Orchestrate collection, transformation, and persistence of security events.

    Collect -> Parse -> Normalize -> Risk Score -> Store

    Persistence is delegated to IngestionService; this class does not
    perform direct database writes.
    """

    def __init__(
        self,
        session: Session,
        *,
        collector_service: CollectorService | None = None,
        transform_service: TransformService | None = None,
        ingestion_service: IngestionService | None = None,
    ) -> None:
        self._collector = collector_service or CollectorService()
        self._transform = transform_service or TransformService()
        self._ingestion = ingestion_service or IngestionService(session)

    def process_raw_logs(
        self,
        *,
        secure_lines: list[str] | None = None,
        audit_lines: list[str] | None = None,
        hostname: str | None = None,
        server_id: str | None = None,
        owner_id: str | None = None,
        system_metrics: dict[str, float] | None = None,
        source_lines: dict[str, list[str]] | None = None,
    ) -> dict[str, Any]:
        """Run the full pipeline on raw secure and audit log lines."""
        secure_count = len(secure_lines or [])
        audit_count = len(audit_lines or [])
        processed = secure_count + audit_count
        if source_lines:
            processed = max(processed, sum(len(lines or []) for lines in source_lines.values()))

        logger.info(
            "Pipeline processing raw logs host=%r secure_lines=%d audit_lines=%d",
            hostname,
            secure_count,
            audit_count,
        )

        normalized, transform_errors = self._transform.normalize_log_lines(
            secure_lines=secure_lines,
            audit_lines=audit_lines,
            hostname=hostname,
        )
        failed_login_count = self._count_failed_logins(normalized)
        normalized.extend(
            self._generic_events_from_sources(
                source_lines or {},
                hostname=hostname,
            )
        )
        events = self._transform.enrich_events(
            normalized,
            failed_login_count=failed_login_count,
        )

        return self._store_events(
            events,
            processed=processed,
            transform_errors=transform_errors,
            server_id=server_id,
            owner_id=owner_id,
            system_metrics=system_metrics,
            failed_login_count=failed_login_count,
        )

    def process_parsed_events(
        self,
        events: list[dict[str, Any] | str | None],
        *,
        source: str = "secure",
        hostname: str | None = None,
        server_id: str | None = None,
    ) -> dict[str, Any]:
        """Run the pipeline on already parsed events or raw line strings."""
        processed = len(events)
        logger.info("Pipeline processing %d parsed/raw items", processed)

        if hostname:
            self._transform = TransformService(default_hostname=hostname)

        normalized, transform_errors = self._transform.normalize_batch(
            events,
            source="audit" if source == "audit" else "secure",
        )
        failed_login_count = self._count_failed_logins(normalized)
        scored = self._transform.enrich_events(
            normalized,
            failed_login_count=failed_login_count,
        )

        return self._store_events(
            scored,
            processed=processed,
            transform_errors=transform_errors,
            server_id=server_id,
        )

    def process_single_raw_line(
        self,
        raw_line: str,
        *,
        source: str = "secure",
        hostname: str | None = None,
    ) -> dict[str, Any]:
        """Run the pipeline for a single raw log line."""
        if hostname:
            self._transform = TransformService(default_hostname=hostname)

        processed = 1
        try:
            normalized = self._transform.normalize_raw_line(
                raw_line,
                source="audit" if source == "audit" else "secure",
            )
        except Exception as exc:
            logger.exception("Pipeline failed to normalize single raw line")
            return self._build_stats(
                processed=processed,
                failed=1,
                transform_errors=[{"index": 0, "error": str(exc)}],
            )

        if normalized is None:
            return self._build_stats(
                processed=processed,
                skipped=1,
                transform_errors=[{"index": 0, "error": "Unrecognized or unsupported log line"}],
            )

        scored = self._transform.enrich_events(normalized=[normalized], failed_login_count=0)
        return self._store_events(
            scored,
            processed=processed,
            transform_errors=[],
        )

    def process_single_parsed_event(
        self,
        parsed: dict[str, Any],
        *,
        hostname: str | None = None,
    ) -> dict[str, Any]:
        """Run the pipeline for a single already-parsed log event."""
        if hostname:
            self._transform = TransformService(default_hostname=hostname)

        processed = 1
        try:
            normalized = self._transform.normalize_parsed(parsed)
        except Exception as exc:
            logger.exception("Pipeline failed to normalize single parsed event")
            return self._build_stats(
                processed=processed,
                failed=1,
                transform_errors=[{"index": 0, "error": str(exc)}],
            )

        if normalized is None:
            return self._build_stats(
                processed=processed,
                skipped=1,
                transform_errors=[{"index": 0, "error": "Event type not supported by normalizer"}],
            )

        scored = self._transform.enrich_events(normalized=[normalized], failed_login_count=0)
        return self._store_events(
            scored,
            processed=processed,
            transform_errors=[],
        )

    def collect_and_process(
        self,
        config: SSHConfig,
        *,
        tail_lines: int | None = None,
        log_sources: frozenset[str] | None = None,
        server_id: str | None = None,
        owner_id: str | None = None,
        server_name: str | None = None,
    ) -> dict[str, Any]:
        """Collect raw logs from a Linux host and run the full pipeline."""
        logger.info("Pipeline collect_and_process host=%s server_id=%s", config.host, server_id)
        try:
            payload = self._collector.collect_raw_lines(
                config,
                tail_lines=tail_lines,
                log_sources=log_sources,
            )
        except Exception as exc:
            logger.exception("Log collection failed for host=%s", config.host)
            return self._build_stats(
                processed=0,
                transform_errors=[{"stage": "collect", "error": str(exc)}],
                failed=1,
            )

        sources = log_sources or frozenset({"secure", "audit"})
        secure_lines = payload.get("secure_lines") if ("secure" in sources or "auth" in sources or "last" in sources or "lastb" in sources or "who" in sources or not log_sources) else []
        audit_lines = payload.get("audit_lines") if ("audit" in sources or "syslog" in sources or "journalctl" in sources or not log_sources) else []
        if not log_sources:
            secure_lines = payload.get("secure_lines", [])
            audit_lines = payload.get("audit_lines", [])

        return self.process_raw_logs(
            secure_lines=secure_lines,
            audit_lines=audit_lines,
            hostname=server_name or payload.get("host"),
            server_id=server_id,
            owner_id=owner_id,
            system_metrics=payload.get("metrics"),
            source_lines=payload.get("sources"),
        )

    def collect_logs(
        self,
        server_id: str,
        *,
        tail_lines: int | None = None,
        log_sources: frozenset[str] | None = None,
    ) -> dict[str, Any]:
        """Collect and process logs for a server ID (database credentials only)."""
        from backend.database import server_crud
        from backend.services.ssh_service import SSHService

        session = self._ingestion._session
        server = server_crud.get_server(session, server_id)
        if server is None:
            raise ValueError(f"Server '{server_id}' not found.")
        config = SSHService.config_from_server(server)
        return self.collect_and_process(
            config,
            tail_lines=tail_lines,
            log_sources=log_sources,
            server_id=server.id,
            owner_id=server.owner_id or server.created_by,
            server_name=server.server_name,
        )

    @staticmethod
    def _count_failed_logins(events: list[NormalizedSecurityEvent]) -> int:
        """Compute batch context passed into the stateless RiskEngine."""
        return sum(1 for event in events if event.event_type == EventType.FAILED_LOGIN)

    @staticmethod
    def _generic_events_from_sources(
        source_lines: dict[str, list[str]],
        *,
        hostname: str | None = None,
    ) -> list[NormalizedSecurityEvent]:
        """Create normalized records for command outputs not covered by auth/audit parsers."""
        generic_sources = {
            "journalctl", "uptime", "free", "df", "ps", "ss", "top", "hostnamectl", "uname", "who", "w", "last", "lastb"
        }
        source_commands = {
            "journalctl": "journalctl -n 500 --no-pager",
            "last": "last",
            "lastb": "lastb",
            "who": "who",
            "w": "w",
            "uptime": "uptime",
            "free": "free -m",
            "df": "df -h",
            "ps": "ps aux",
            "ss": "ss -tuln",
            "hostnamectl": "hostnamectl",
            "uname": "uname -a",
            "top": "top",
        }
        events: list[NormalizedSecurityEvent] = []
        now = datetime.now(timezone.utc).isoformat()
        for source, lines in source_lines.items():
            if source not in generic_sources:
                continue
            for index, line in enumerate(lines or [], start=1):
                if not line.strip():
                    continue
                event_type = EventType.COMMAND_EXECUTION
                severity = "info"
                risk_score = 5
                username = None
                if source == "lastb":
                    event_type = EventType.FAILED_LOGIN
                    severity = "medium"
                    risk_score = 55
                    username = line.split()[0] if line.split() else None
                elif source in {"last", "who", "w"}:
                    event_type = EventType.SUCCESSFUL_LOGIN
                    severity = "low"
                    risk_score = 15
                    username = line.split()[0] if line.split() else None
                command = source_commands.get(source, source)
                events.append(
                    NormalizedSecurityEvent(
                        event_id=str(uuid.uuid4()),
                        timestamp=now,
                        hostname=hostname or "unknown",
                        username=username,
                        source_ip=None,
                        event_type=event_type,
                        category=category_for(event_type),
                        severity=severity,
                        risk_score=risk_score,
                        raw_log=line,
                        metadata={
                            "source": source,
                            "line_number": index,
                            "normalized_data": {
                                "source": source,
                                "line": line,
                                "command": command,
                            },
                            "command": command,
                            "message": line,
                        },
                    )
                )
        return events

    def _store_events(
        self,
        events: list[NormalizedSecurityEvent],
        *,
        processed: int,
        transform_errors: list[dict[str, Any]],
        server_id: str | None = None,
        owner_id: str | None = None,
        system_metrics: dict[str, float] | None = None,
        failed_login_count: int = 0,
    ) -> dict[str, Any]:
        """Delegate persistence to IngestionService."""
        skipped = max(0, processed - len(events) - len(transform_errors))

        if not events:
            return self._build_stats(
                processed=processed,
                skipped=skipped,
                transform_errors=transform_errors,
            )

        payloads = [event.to_persistence_dict() for event in events]
        if server_id:
            for payload in payloads:
                payload["server_id"] = server_id
        if owner_id:
            for payload in payloads:
                payload["owner_id"] = owner_id
        if system_metrics:
            for payload in payloads:
                payload.setdefault("cpu_usage", system_metrics.get("cpu_usage"))
                payload.setdefault("memory_usage", system_metrics.get("memory_usage"))
                payload.setdefault("disk_usage", system_metrics.get("disk_usage"))
                payload.setdefault("network_connections", int(system_metrics.get("network_connections", 0)))
        if failed_login_count:
            for payload in payloads:
                payload.setdefault("failed_login_count", failed_login_count)
        for payload in payloads:
            metadata = payload.get("metadata") or {}
            if metadata.get("normalized_data"):
                import json
                payload["normalized_data"] = json.dumps(metadata["normalized_data"], default=str)
        try:
            ingest_stats = self._ingestion.ingest_bulk_events(payloads)
        except Exception as exc:
            logger.exception("Pipeline bulk ingestion failed")
            return self._build_stats(
                processed=processed,
                skipped=skipped,
                transform_errors=transform_errors + [{"stage": "store", "error": str(exc)}],
                failed=len(events),
            )

        return self._build_stats(
            processed=processed,
            inserted=ingest_stats.get("inserted", 0),
            duplicates=ingest_stats.get("duplicates", 0),
            failed=len(transform_errors) + ingest_stats.get("failed", 0),
            skipped=skipped,
            transform_errors=transform_errors + ingest_stats.get("errors", []),
        )

    @staticmethod
    def _build_stats(
        *,
        processed: int,
        inserted: int = 0,
        failed: int = 0,
        duplicates: int = 0,
        skipped: int = 0,
        transform_errors: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return {
            "processed": processed,
            "inserted": inserted,
            "failed": failed,
            "duplicates": duplicates,
            "skipped": skipped,
            "errors": transform_errors or [],
        }
