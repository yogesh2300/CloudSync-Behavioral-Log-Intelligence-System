"""Paramiko SSH client wrapper for remote log file access."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Generator, List, Optional

import paramiko

from backend.collector.config import SSHConfig


class SSHClient:
    """Manages Paramiko SSH and SFTP sessions to a CentOS Stream VM."""

    def __init__(self, config: SSHConfig) -> None:
        self._config = config
        self._client: Optional[paramiko.SSHClient] = None
        self._sftp: Optional[paramiko.SFTPClient] = None

    def connect(self) -> None:
        """Open SSH and SFTP connections using the configured credentials."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs = {
            "hostname": self._config.host,
            "port": self._config.port,
            "username": self._config.username,
            "timeout": self._config.timeout,
            "allow_agent": False,
            "look_for_keys": False,
        }

        if self._config.private_key_path:
            key_path = Path(self._config.private_key_path)
            connect_kwargs["key_filename"] = str(key_path)
        else:
            connect_kwargs["password"] = self._config.password

        client.connect(**connect_kwargs)
        self._client = client
        self._sftp = client.open_sftp()

    def disconnect(self) -> None:
        """Close SFTP and SSH sessions."""
        if self._sftp is not None:
            self._sftp.close()
            self._sftp = None
        if self._client is not None:
            self._client.close()
            self._client = None

    def read_remote_lines(self, remote_path: str, tail_lines: Optional[int] = None) -> List[str]:
        """
        Read a remote log file line by line.

        When tail_lines is set, only the last N non-empty lines are returned.
        This avoids loading very large audit logs entirely into memory.
        """
        if self._sftp is None:
            raise RuntimeError("SSH client is not connected. Call connect() first.")

        with self._sftp.open(remote_path, "r") as remote_file:
            text_lines = [
                line.rstrip("\r\n")
                for line in remote_file.readlines()
                if line.strip()
            ]

        if tail_lines is not None and tail_lines > 0:
            return text_lines[-tail_lines:]
        return text_lines

    @contextmanager
    def session(self) -> Generator["SSHClient", None, None]:
        """Context manager that connects on entry and disconnects on exit."""
        self.connect()
        try:
            yield self
        finally:
            self.disconnect()


@contextmanager
def ssh_session(config: SSHConfig) -> Generator[SSHClient, None, None]:
    """Convenience context manager for a configured SSH session."""
    client = SSHClient(config)
    with client.session():
        yield client
