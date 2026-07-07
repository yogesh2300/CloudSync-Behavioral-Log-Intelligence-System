"""PostgreSQL connection and session management for DefenSync."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.core.config import get_settings


def get_database_url() -> str:
    """Return the PostgreSQL connection URL from application settings."""
    return get_settings().DATABASE_URL


@lru_cache(maxsize=1)
def get_engine(*, echo: bool | None = None) -> Engine:
    """Return a cached SQLAlchemy 2.x engine configured for PostgreSQL."""
    if echo is None:
        echo = os.getenv("DB_ECHO", "false").lower() in {"1", "true", "yes"}

    return create_engine(
        get_database_url(),
        echo=echo,
        pool_pre_ping=True,
    )


def get_session_factory(*, echo: bool | None = None) -> sessionmaker[Session]:
    """Return a session factory bound to the application engine."""
    return sessionmaker(
        bind=get_engine(echo=echo),
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )


def get_session(*, echo: bool | None = None) -> Session:
    """Create a new database session."""
    return get_session_factory(echo=echo)()


def session_scope(*, echo: bool | None = None) -> Iterator[Session]:
    """Provide a transactional scope that commits on success and rolls back on failure."""
    session = get_session(echo=echo)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
