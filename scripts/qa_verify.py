#!/usr/bin/env python3
"""Quick QA verification script for DefenSync (read-only API checks)."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

BASE = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
ADMIN_USER = os.getenv("QA_ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("QA_ADMIN_PASS", "Admin@123")


def req(method: str, path: str, data=None, token=None, form=False):
    url = f"{BASE}{path}"
    headers = {}
    body = None
    if data is not None:
        if form:
            body = urllib.parse.urlencode(data).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            body = json.dumps(data).encode()
            headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"detail": raw}
        return exc.code, payload
    except Exception as exc:
        return 0, {"detail": str(exc)}


def main() -> int:
    results: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, info: str = "") -> None:
        results.append((name, ok, info))
        status = "PASS" if ok else "FAIL"
        print(f"{status}\t{name}\t{info}")

    # DB offline checks
    from backend.database.connection import get_engine
    from sqlalchemy import inspect, text

    engine = get_engine()
    tables = set(inspect(engine).get_table_names())
    required = {"users", "servers", "events", "alerts", "detections", "collection_runs"}
    check("database_tables", required.issubset(tables), f"tables={sorted(tables)}")
    with engine.connect() as conn:
        counts = {t: conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar() for t in required}
    check("database_counts", all(v is not None for v in counts.values()), str(counts))

    # API health
    code, body = req("GET", "/health")
    check("api_health", code == 200 and body.get("status") == "healthy", str(code))

    # Admin auth
    code, body = req("POST", "/api/v1/auth/token", {"username": ADMIN_USER, "password": ADMIN_PASS}, form=True)
    admin_token = body.get("access_token") if code == 200 else None
    check("admin_login", code == 200 and bool(admin_token), str(code))

    if not admin_token:
        print("\nCannot continue API checks without admin token.")
        return 1

    code, me = req("GET", "/api/v1/auth/me", token=admin_token)
    check("admin_role", code == 200 and str(me.get("role", "")).upper() == "ADMIN", me.get("role", ""))

    admin_eps = [
        ("/api/v1/admin/dashboard", "admin_dashboard"),
        ("/api/v1/admin/users", "admin_users"),
        ("/api/v1/admin/servers", "admin_servers"),
        ("/api/v1/admin/events?limit=5", "admin_events"),
        ("/api/v1/admin/alerts?limit=5", "admin_alerts"),
        ("/api/v1/admin/alerts/summary", "admin_alerts_summary"),
        ("/api/v1/admin/detections?limit=5", "admin_detections"),
        ("/api/v1/admin/detections/status", "admin_detection_status"),
        ("/api/v1/admin/collections?limit=5", "admin_collections"),
        ("/api/v1/admin/analytics", "admin_analytics"),
        ("/api/v1/admin/system-health", "admin_system_health"),
        ("/api/v1/admin/ml", "admin_ml"),
    ]
    for path, name in admin_eps:
        code, body = req("GET", path, token=admin_token)
        ok = code == 200
        extra = ""
        if name == "admin_dashboard" and ok:
            extra = f"events={body.get('summary', {}).get('total_events')}"
        elif name == "admin_events" and ok:
            extra = f"total={body.get('total')}"
        check(name, ok, f"{code} {extra}")

    # Analyst endpoints as admin (should still work; admin sees all)
    for path, name in [
        ("/api/v1/dashboard", "dashboard"),
        ("/api/v1/events?limit=5", "events"),
        ("/api/v1/events/stats", "event_stats"),
        ("/api/v1/alerts?limit=5", "alerts"),
        ("/api/v1/alerts/summary", "alerts_summary"),
        ("/api/v1/detection/status", "detection_status"),
        ("/api/v1/detection/anomalies?limit=5", "anomalies"),
        ("/api/v1/servers", "servers"),
        ("/api/v1/health/servers", "fleet_health"),
    ]:
        code, body = req("GET", path, token=admin_token)
        check(name, code == 200, str(code))

    # RBAC: no token
    code, _ = req("GET", "/api/v1/events")
    check("rbac_no_token", code == 401, str(code))

    # ML duplicate check via DB
    with engine.connect() as conn:
        dup_alerts = conn.execute(
            text("SELECT event_id, COUNT(*) c FROM alerts GROUP BY event_id HAVING COUNT(*) > 1")
        ).fetchall()
        dup_det = conn.execute(
            text("SELECT event_id, COUNT(*) c FROM detections GROUP BY event_id HAVING COUNT(*) > 1")
        ).fetchall()
    check("no_duplicate_alerts_per_event", len(dup_alerts) == 0, f"dupes={len(dup_alerts)}")
    check("no_duplicate_detections_per_event", len(dup_det) == 0, f"dupes={len(dup_det)}")

    failed = [r for r in results if not r[1]]
    print(f"\nTotal: {len(results)} checks, {len(results)-len(failed)} passed, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
