"""SSH log collection package for DefenSync."""

from backend.collector.config import SSHConfig
from backend.collector.log_sources import DEFAULT_LOG_SOURCES, LOG_SOURCE_CATALOG

__all__ = ["SSHConfig", "DEFAULT_LOG_SOURCES", "LOG_SOURCE_CATALOG"]
