"""SSH connection configuration for the log collector."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class SSHConfig:
    """Credentials and connection settings for a CentOS Stream VM."""

    host: str
    username: str
    port: int = 22
    password: Optional[str] = None
    private_key_path: Optional[Path] = None
    timeout: float = 30.0

    def __post_init__(self) -> None:
        if not self.password and not self.private_key_path:
            raise ValueError("Either password or private_key_path must be provided.")
