#!/usr/bin/env python3
"""Seed DefenSync with demo security events for dashboard and ML detection testing."""

from __future__ import annotations

import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv()

from backend.database.connection import get_session
from backend.services.ingestion_service import IngestionService

HOSTS = ["cloud-node-01", "cloud-node-02", "web-server-prod"]
USERS = ["admin", "root", "deploy", "guest", "alice", "bob"]
IPS = ["192.168.1.10", "192.168.1.55", "203.0.113.8", "10.0.0.42", "45.33.32.156", "127.0.0.1"]

TEMPLATES = [
    ("Failed Login", "authentication", "medium", 55, "Failed password for {user} from {ip} port 22 ssh2"),
    ("Failed Login", "authentication", "high", 78, "Failed password for invalid user {user} from {ip}"),
    ("Successful Login", "authentication", "low", 15, "Accepted password for {user} from {ip} port 22"),
    ("Sudo Command", "privilege", "high", 82, "{user} : TTY=pts/0 ; USER=root ; COMMAND=/usr/bin/chmod 777 /etc/shadow"),
    ("User Creation", "account", "medium", 60, "new user: name={user}"),
    ("Invalid User", "authentication", "medium", 50, "Invalid user {user} from {ip}"),
    ("Successful Login", "authentication", "high", 72, "Accepted publickey for root from {ip} port 22"),
]


def build_events(count: int = 120) -> list[dict]:
    events = []
    now = datetime.now(timezone.utc)
    for i in range(count):
        etype, category, severity, risk, msg_tpl = random.choice(TEMPLATES)
        user = random.choice(USERS)
        ip = random.choice(IPS)
        host = random.choice(HOSTS)
        ts = now - timedelta(hours=random.randint(0, 48), minutes=random.randint(0, 59))
        if etype == "Failed Login" and random.random() < 0.3:
            risk = min(100, risk + random.randint(10, 25))
            severity = "high" if risk >= 70 else severity
        message = msg_tpl.format(user=user, ip=ip)
        raw = f"{ts.strftime('%b %d %H:%M:%S')} {host} sshd[{random.randint(1000,9999)}]: {message}"
        events.append({
            "event_id": str(uuid.uuid4()),
            "timestamp": ts.isoformat(),
            "hostname": host,
            "username": user,
            "source_ip": ip,
            "event_type": etype,
            "category": category,
            "severity": severity,
            "risk_score": risk,
            "process": "sshd" if "ssh" in message.lower() or "password" in message.lower() else "sudo",
            "message": message,
            "raw_log": raw,
        })
    return events


def main() -> int:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    session = get_session()
    try:
        service = IngestionService(session)
        payloads = build_events(count)
        stats = service.ingest_bulk_events(payloads)
        print(f"Seed complete: inserted={stats['inserted']} duplicates={stats['duplicates']} failed={stats['failed']}")
        if stats["errors"]:
            print("Errors:", stats["errors"][:5])
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
