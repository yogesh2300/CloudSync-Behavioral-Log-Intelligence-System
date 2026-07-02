"""SSH log collector for CentOS Stream security and audit logs."""

from backend.collector.config import SSHConfig
from backend.collector.log_collector import LogCollector, collect_logs

__all__ = ["SSHConfig", "LogCollector", "collect_logs"]
