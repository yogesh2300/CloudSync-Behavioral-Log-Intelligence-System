"""PostgreSQL connection and session management for CloudSync."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Iterator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()


def _require_env(name: str) -> str:
    """Return a required database environment variable."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable {name}. "
            "Set it in your .env file before connecting to PostgreSQL."
        )
    return value


def get_database_url() -> str:
    """Build a PostgreSQL connection URL from .env variables."""
    host = _require_env("DB_HOST")
    port = _require_env("DB_PORT")
    name = _require_env("DB_NAME")
    user = _require_env("DB_USER")
    password = _require_env("DB_PASSWORD")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"


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
