"""Collect and parse security logs from a CentOS Stream VM over SSH."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.collector.config import SSHConfig
from backend.collector.parsers import parse_audit_line, parse_secure_line
from backend.collector.ssh_client import SSHClient, ssh_session

SECURE_LOG_PATH = "/var/log/secure"
AUDIT_LOG_PATH = "/var/log/audit/audit.log"


class LogCollector:
    """Reads CentOS Stream security logs via SSH and returns structured JSON."""

    def __init__(self, config: SSHConfig) -> None:
        self._config = config

    def collect(self, tail_lines: Optional[int] = None) -> Dict[str, Any]:
        """
        Connect to the VM, read secure and audit logs, and return a JSON object.

        Args:
            tail_lines: If set, only the last N lines from each log file are read.

        Returns:
            A dictionary suitable for json.dumps(), containing metadata and
            parsed log entries grouped by source.
        """
        with ssh_session(self._config) as client:
            secure_lines = client.read_remote_lines(SECURE_LOG_PATH, tail_lines=tail_lines)
            audit_lines = client.read_remote_lines(AUDIT_LOG_PATH, tail_lines=tail_lines)

        return build_collection_result(
            host=self._config.host,
            secure_lines=secure_lines,
            audit_lines=audit_lines,
        )

    def collect_json(self, tail_lines: Optional[int] = None, indent: Optional[int] = 2) -> str:
        """Return collected logs as a formatted JSON string."""
        return json.dumps(self.collect(tail_lines=tail_lines), indent=indent)


def build_collection_result(
    host: str,
    secure_lines: List[str],
    audit_lines: List[str],
) -> Dict[str, Any]:
    """Build the top-level JSON payload from raw log lines."""
    secure_entries = [
        parse_secure_line(line, line_number=index)
        for index, line in enumerate(secure_lines, start=1)
    ]
    audit_entries = [
        parse_audit_line(line, line_number=index)
        for index, line in enumerate(audit_lines, start=1)
    ]

    return {
        "host": host,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "logs": {
            "secure": secure_entries,
            "audit": audit_entries,
        },
        "summary": {
            "secure_count": len(secure_entries),
            "audit_count": len(audit_entries),
            "secure_path": SECURE_LOG_PATH,
            "audit_path": AUDIT_LOG_PATH,
        },
    }


def collect_logs(
    host: str,
    username: str,
    *,
    password: Optional[str] = None,
    private_key_path: Optional[str] = None,
    port: int = 22,
    tail_lines: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Convenience function to collect logs with minimal setup.

    Example:
        result = collect_logs(
            host="192.168.1.10",
            username="centos",
            password="secret",
            tail_lines=100,
        )
    """
    config = SSHConfig(
        host=host,
        username=username,
        port=port,
        password=password,
        private_key_path=private_key_path,
    )
    return LogCollector(config).collect(tail_lines=tail_lines)
