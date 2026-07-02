"""CloudSync CLI entry point."""

from __future__ import annotations

import json
import os
from getpass import getpass
from pathlib import Path
from typing import Any

from backend.collector.config import SSHConfig
from backend.collector.log_collector import AUDIT_LOG_PATH, SECURE_LOG_PATH
from backend.collector.parsers import parse_logs, summarize_events
from backend.collector.ssh_client import ssh_session
from backend.database.init_db import create_tables
from backend.normalizer import EventNormalizer


class PipelineState:
    """In-memory state shared across CLI pipeline steps."""

    def __init__(self) -> None:
        self.ssh_config: SSHConfig | None = None
        self.raw_secure_lines: list[str] = []
        self.raw_audit_lines: list[str] = []
        self.parsed_logs: list[dict[str, Any]] = []
        self.normalized_events: list[Any] = []


state = PipelineState()


def print_header(title: str) -> None:
    print(f"\n=== {title} ===")


def prompt_tail_lines() -> int | None:
    raw = input("Tail lines (blank = all): ").strip()
    if not raw:
        return None
    try:
        value = int(raw)
        return value if value > 0 else None
    except ValueError:
        print("Invalid number; reading all lines.")
        return None


def load_ssh_config() -> SSHConfig:
    """Build SSH config from environment variables or interactive prompts."""
    host = os.getenv("SSH_HOST") or input("SSH host: ").strip()
    username = os.getenv("SSH_USER") or input("SSH username: ").strip()
    port = int(os.getenv("SSH_PORT", "22"))

    private_key_path = os.getenv("SSH_PRIVATE_KEY_PATH")
    if private_key_path:
        return SSHConfig(
            host=host,
            username=username,
            port=port,
            private_key_path=Path(private_key_path),
        )

    password = os.getenv("SSH_PASSWORD")
    if not password:
        password = getpass("SSH password: ")

    return SSHConfig(host=host, username=username, port=port, password=password)


def test_ssh_connection() -> None:
    print_header("Test SSH Connection")
    config = load_ssh_config()
    try:
        with ssh_session(config) as client:
            secure_sample = client.read_remote_lines(SECURE_LOG_PATH, tail_lines=1)
            print(f"Connected to {config.host} as {config.username}.")
            if secure_sample:
                print(f"Sample secure log line: {secure_sample[0][:120]}")
            else:
                print("Secure log is empty or unreadable.")
        state.ssh_config = config
    except Exception as exc:
        print(f"SSH connection failed: {exc}")


def read_logs() -> None:
    print_header("Read Logs")
    config = state.ssh_config or load_ssh_config()
    tail_lines = prompt_tail_lines()

    try:
        with ssh_session(config) as client:
            state.raw_secure_lines = client.read_remote_lines(
                SECURE_LOG_PATH,
                tail_lines=tail_lines,
            )
            state.raw_audit_lines = client.read_remote_lines(
                AUDIT_LOG_PATH,
                tail_lines=tail_lines,
            )
        state.ssh_config = config
        print(f"Read {len(state.raw_secure_lines)} secure log lines.")
        print(f"Read {len(state.raw_audit_lines)} audit log lines.")
    except Exception as exc:
        print(f"Failed to read logs: {exc}")


def parse_logs_menu() -> None:
    print_header("Parse Logs")
    if not state.raw_secure_lines and not state.raw_audit_lines:
        print("No raw logs in memory. Choose option 2 first or reading now...")
        read_logs()
        if not state.raw_secure_lines and not state.raw_audit_lines:
            return

    state.parsed_logs = parse_logs(state.raw_secure_lines, state.raw_audit_lines)

    total_raw = len(state.raw_secure_lines) + len(state.raw_audit_lines)
    ignored = total_raw - len(state.parsed_logs)
    summary = summarize_events(state.parsed_logs)

    print(f"Parsed {len(state.parsed_logs)} supported events from {total_raw} raw lines.")
    print(f"Ignored {ignored} unsupported or unrecognized lines.")

    if summary:
        print("\nEvent summary:")
        for event_type, count in sorted(summary.items()):
            print(f"  {event_type}: {count}")

    if state.parsed_logs:
        print("\nParsed events (JSON):")
        print(json.dumps(state.parsed_logs, indent=2, ensure_ascii=False))
    else:
        print("\nNo supported security events found in the collected logs.")


def normalize_events() -> None:
    print_header("Normalize Events")
    if not state.parsed_logs:
        print("No parsed logs in memory. Running parse step first...")
        parse_logs_menu()
        if not state.parsed_logs:
            return

    hostname = state.ssh_config.host if state.ssh_config else "unknown"
    normalizer = EventNormalizer(default_hostname=hostname)
    state.normalized_events = normalizer.normalize_many(state.parsed_logs)

    print(f"Normalized {len(state.normalized_events)} security events.")
    for event in state.normalized_events[:5]:
        print(
            f"  [{event.severity}] {event.event_type.value} "
            f"user={event.username} risk={event.risk_score}"
        )
    if len(state.normalized_events) > 5:
        print(f"  ... and {len(state.normalized_events) - 5} more")


def initialize_database() -> None:
    print_header("Initialize Database")
    try:
        create_tables()
        print("Database schema initialized successfully.")
    except Exception as exc:
        print(f"Database initialization failed: {exc}")


def print_menu() -> None:
    print(
        "\nCloudSync - Behavioral Log Intelligence System\n"
        "1 - Test SSH Connection\n"
        "2 - Read Logs\n"
        "3 - Parse Logs\n"
        "4 - Normalize Events\n"
        "5 - Initialize Database\n"
        "6 - Exit"
    )


def main() -> int:
    actions = {
        "1": test_ssh_connection,
        "2": read_logs,
        "3": parse_logs_menu,
        "4": normalize_events,
        "5": initialize_database,
    }

    while True:
        print_menu()
        choice = input("Select an option: ").strip()

        if choice == "6":
            print("Goodbye.")
            return 0

        action = actions.get(choice)
        if action is None:
            print("Invalid option. Please choose 1-6.")
            continue

        try:
            action()
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
        except Exception as exc:
            print(f"Unexpected error: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
