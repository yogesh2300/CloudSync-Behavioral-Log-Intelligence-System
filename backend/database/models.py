"""SQLAlchemy ORM models for CloudSync."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all CloudSync ORM models."""


class SecurityEvent(Base):
    """Persisted security event from the CloudSync pipeline."""

    __tablename__ = "security_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    source_ip: Mapped[str | None] = mapped_column(String(45), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    process: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_log: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_security_events_risk_score_timestamp", "risk_score", "timestamp"),
        Index("ix_security_events_username_timestamp", "username", "timestamp"),
        Index("ix_security_events_type_timestamp", "event_type", "timestamp"),
    )

    def __repr__(self) -> str:
        return (
            f"SecurityEvent(id={self.id!r}, event_id={self.event_id!r}, "
            f"event_type={self.event_type!r}, risk_score={self.risk_score!r})"
        )
