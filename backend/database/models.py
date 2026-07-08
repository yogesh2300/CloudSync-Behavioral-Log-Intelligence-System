"""SQLAlchemy database models for DefenSync."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    """Database model for registered system accounts."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True, nullable=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="ANALYST")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class Server(Base):
    """Linux server registered for SSH log collection and behavioral monitoring."""
    __tablename__ = "servers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    server_name = Column(String(100), nullable=False, index=True)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False, default=22)
    username = Column(String(100), nullable=False)
    authentication_type = Column(String(20), nullable=False, default="password")
    encrypted_password = Column(Text, nullable=True)
    encrypted_private_key = Column(Text, nullable=True)
    operating_system = Column(String(50), nullable=True, default="linux")
    environment = Column(String(20), nullable=False, default="production")
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="active")
    health_status = Column(String(30), nullable=False, default="unknown")
    connection_latency_ms = Column(Integer, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    last_connected = Column(DateTime, nullable=True)
    last_health_check = Column(DateTime, nullable=True)
    last_successful_collection = Column(DateTime, nullable=True)
    health_error_message = Column(Text, nullable=True)
    consecutive_failures = Column(Integer, nullable=False, default=0)
    owner_id = Column(String(36), nullable=True, index=True)
    created_by = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class CollectionRun(Base):
    """Record of a log collection execution against a server."""
    __tablename__ = "collection_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    server_id = Column(String(36), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="running")
    processed = Column(Integer, nullable=False, default=0)
    inserted = Column(Integer, nullable=False, default=0)
    duplicates = Column(Integer, nullable=False, default=0)
    failed = Column(Integer, nullable=False, default=0)
    skipped = Column(Integer, nullable=False, default=0)
    duration_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)


class Event(Base):
    """Database model for normalized security logs."""
    __tablename__ = "events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), unique=True, nullable=False, index=True)
    server_id = Column(String(36), nullable=True, index=True)
    owner_id = Column(String(36), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    hostname = Column(String(100), nullable=False)
    username = Column(String(100), nullable=True)
    source_ip = Column(String(45), nullable=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, index=True)
    risk_score = Column(Integer, nullable=False, index=True)
    risk_level = Column(String(20), nullable=True, index=True)
    command = Column(Text, nullable=True)
    process = Column(String(50), nullable=True)
    message = Column(Text, nullable=False)
    raw_log = Column(Text, nullable=False)
    normalized_data = Column(Text, nullable=True)
    hash = Column(String(64), unique=True, nullable=False, index=True)
    cpu_usage = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    disk_usage = Column(Float, nullable=True)
    login_time = Column(DateTime, nullable=True)
    logout_time = Column(DateTime, nullable=True)
    failed_login_count = Column(Integer, nullable=True)
    session_duration = Column(Float, nullable=True)
    commands_executed = Column(Integer, nullable=True)
    network_connections = Column(Integer, nullable=True)


class Alert(Base):
    """Security alert raised from rule-based or ML detection."""
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), unique=True, nullable=False, index=True)
    server_id = Column(String(36), nullable=True, index=True)
    owner_id = Column(String(36), nullable=True, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, index=True)
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String(20), nullable=True)
    detection_type = Column(String(50), nullable=False, default="rule_based")
    acknowledged = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class Detection(Base):
    """Stored ML prediction result for a security event."""
    __tablename__ = "detections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    server_id = Column(String(36), nullable=False, index=True)
    owner_id = Column(String(36), nullable=True, index=True)
    event_id = Column(String(36), nullable=False, index=True)
    isolation_score = Column(Float, nullable=True)
    random_forest_label = Column(String(20), nullable=True)
    classification = Column(String(20), nullable=True)
    confidence = Column(Float, nullable=True)
    detection_type = Column(String(50), nullable=True)
    message = Column(Text, nullable=True)
    is_anomaly = Column(Boolean, nullable=False, default=False)
    risk_score = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


SecurityEvent = Event
MLPrediction = Detection

Index("ix_events_user_time", Event.username, Event.timestamp)
Index("ix_events_severity_time", Event.severity, Event.timestamp)
Index("ix_events_server_time", Event.server_id, Event.timestamp)
