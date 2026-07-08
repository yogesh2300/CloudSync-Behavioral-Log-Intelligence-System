"""Apply DefenSync schema updates (multi-server platform)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
from sqlalchemy import inspect, text

load_dotenv()

from backend.database.connection import get_engine
from backend.database.models import Base


def _table_exists(conn, name: str) -> bool:
    return inspect(conn).has_table(name)


def migrate() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        if _table_exists(conn, "security_events") and not _table_exists(conn, "events"):
            conn.execute(text("ALTER TABLE security_events RENAME TO events"))
        if _table_exists(conn, "ml_predictions") and not _table_exists(conn, "detections"):
            conn.execute(text("ALTER TABLE ml_predictions RENAME TO detections"))

        if _table_exists(conn, "events"):
            conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS hash VARCHAR(64)"))
            conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS server_id VARCHAR(36)"))
            conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS owner_id VARCHAR(36)"))
            conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20)"))
            conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS command TEXT"))
            conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS normalized_data TEXT"))
            conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS cpu_usage DOUBLE PRECISION"))
            conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS memory_usage DOUBLE PRECISION"))
            conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS disk_usage DOUBLE PRECISION"))
            conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS login_time TIMESTAMP"))
            conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS logout_time TIMESTAMP"))
            conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS failed_login_count INTEGER"))
            conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS session_duration DOUBLE PRECISION"))
            conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS commands_executed INTEGER"))
            conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS network_connections INTEGER"))
            conn.execute(text("UPDATE events SET hash = md5(raw_log || event_id) WHERE hash IS NULL"))

        if _table_exists(conn, "alerts"):
            conn.execute(text("ALTER TABLE alerts ADD COLUMN IF NOT EXISTS server_id VARCHAR(36)"))
            conn.execute(text("ALTER TABLE alerts ADD COLUMN IF NOT EXISTS owner_id VARCHAR(36)"))
            conn.execute(text("ALTER TABLE alerts ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20)"))
        if _table_exists(conn, "users"):
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR(50)"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)"))
            conn.execute(text("UPDATE users SET name = username WHERE name IS NULL"))
            conn.execute(text("UPDATE users SET password_hash = hashed_password WHERE password_hash IS NULL"))
            conn.execute(text("UPDATE users SET role = upper(role) WHERE role IS NOT NULL"))
        if _table_exists(conn, "servers"):
            conn.execute(text("ALTER TABLE servers ADD COLUMN IF NOT EXISTS environment VARCHAR(20) DEFAULT 'production'"))
            conn.execute(text("ALTER TABLE servers ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP"))
            conn.execute(text("ALTER TABLE servers ADD COLUMN IF NOT EXISTS owner_id VARCHAR(36)"))
            conn.execute(text("ALTER TABLE servers ADD COLUMN IF NOT EXISTS health_status VARCHAR(30) DEFAULT 'unknown'"))
            conn.execute(text("ALTER TABLE servers ADD COLUMN IF NOT EXISTS connection_latency_ms INTEGER"))
            conn.execute(text("ALTER TABLE servers ADD COLUMN IF NOT EXISTS last_health_check TIMESTAMP"))
            conn.execute(text("ALTER TABLE servers ADD COLUMN IF NOT EXISTS last_successful_collection TIMESTAMP"))
            conn.execute(text("ALTER TABLE servers ADD COLUMN IF NOT EXISTS health_error_message TEXT"))
            conn.execute(text("ALTER TABLE servers ADD COLUMN IF NOT EXISTS consecutive_failures INTEGER DEFAULT 0"))
            conn.execute(text("UPDATE servers SET environment = 'production' WHERE environment IS NULL"))
            conn.execute(text("UPDATE servers SET owner_id = created_by WHERE owner_id IS NULL"))
            conn.execute(text("UPDATE servers SET last_seen = last_connected WHERE last_seen IS NULL AND last_connected IS NOT NULL"))
            conn.execute(text("""
                UPDATE servers
                SET health_status = CASE
                    WHEN status = 'online' THEN 'online'
                    WHEN status IN ('offline', 'error') THEN status
                    WHEN status = 'inactive' THEN 'unknown'
                    ELSE COALESCE(health_status, 'unknown')
                END
            """))
            conn.execute(text("""
                UPDATE servers
                SET status = CASE
                    WHEN status = 'inactive' THEN 'inactive'
                    ELSE 'active'
                END
            """))
            conn.execute(text("UPDATE servers SET consecutive_failures = 0 WHERE consecutive_failures IS NULL"))
        if _table_exists(conn, "detections"):
            conn.execute(text("ALTER TABLE detections ADD COLUMN IF NOT EXISTS owner_id VARCHAR(36)"))
            conn.execute(text("ALTER TABLE detections ADD COLUMN IF NOT EXISTS classification VARCHAR(20)"))
            conn.execute(text("ALTER TABLE detections ADD COLUMN IF NOT EXISTS confidence DOUBLE PRECISION"))
            conn.execute(text("ALTER TABLE detections ADD COLUMN IF NOT EXISTS detection_type VARCHAR(50)"))
            conn.execute(text("ALTER TABLE detections ADD COLUMN IF NOT EXISTS message TEXT"))
        if _table_exists(conn, "servers") and _table_exists(conn, "events"):
            conn.execute(text("""
                UPDATE events e
                SET owner_id = s.owner_id
                FROM servers s
                WHERE e.server_id = s.id AND e.owner_id IS NULL
            """))
        if _table_exists(conn, "servers") and _table_exists(conn, "alerts"):
            conn.execute(text("""
                UPDATE alerts a
                SET owner_id = s.owner_id
                FROM servers s
                WHERE a.server_id = s.id AND a.owner_id IS NULL
            """))

        if _table_exists(conn, "monitored_servers") and not _table_exists(conn, "servers"):
            conn.execute(text("""
                CREATE TABLE servers (
                    id VARCHAR(36) PRIMARY KEY,
                    server_name VARCHAR(100) NOT NULL,
                    host VARCHAR(255) NOT NULL,
                    port INTEGER NOT NULL DEFAULT 22,
                    username VARCHAR(100) NOT NULL,
                    authentication_type VARCHAR(20) NOT NULL DEFAULT 'password',
                    encrypted_password TEXT,
                    encrypted_private_key TEXT,
                    operating_system VARCHAR(50) DEFAULT 'linux',
                    environment VARCHAR(20) NOT NULL DEFAULT 'production',
                    description TEXT,
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    last_seen TIMESTAMP,
                    last_connected TIMESTAMP,
                    owner_id VARCHAR(36),
                    created_by VARCHAR(36),
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """))
            conn.execute(text("""
                INSERT INTO servers (
                    id, server_name, host, port, username, authentication_type,
                    encrypted_password, encrypted_private_key, operating_system,
                    environment, description, status, last_seen, last_connected, owner_id, created_by, created_at, updated_at
                )
                SELECT
                    id,
                    name,
                    host,
                    port,
                    username,
                    CASE WHEN auth_type = 'private_key' THEN 'ssh_key' ELSE 'password' END,
                    CASE WHEN auth_type = 'password' THEN encrypted_credential ELSE NULL END,
                    CASE WHEN auth_type = 'private_key' THEN encrypted_credential ELSE NULL END,
                    operating_system,
                    'production',
                    description,
                    CASE
                        WHEN is_active = FALSE THEN 'inactive'
                        WHEN connection_status = 'online' THEN 'online'
                        WHEN connection_status = 'offline' THEN 'offline'
                        WHEN connection_status = 'error' THEN 'error'
                        ELSE 'active'
                    END,
                    last_connected_at,
                    last_connected_at,
                    created_by,
                    created_by,
                    created_at,
                    updated_at
                FROM monitored_servers
            """))
            conn.execute(text("DROP TABLE monitored_servers"))

    print(f"SQLAlchemy metadata tables before create_all: {sorted(Base.metadata.tables.keys())}")
    Base.metadata.create_all(bind=engine)
    print(f"SQLAlchemy metadata tables after create_all: {sorted(Base.metadata.tables.keys())}")
    print("DefenSync schema migration complete.")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as exc:
        print(f"Migration failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
