"""Initialize DefenSync PostgreSQL schema."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Sequence

from dotenv import load_dotenv

from backend.database.connection import get_engine
from backend.database.models import Base

logger = logging.getLogger(__name__)


def create_tables(*, echo: bool = False) -> None:
    """Create all database tables defined on the declarative Base."""
    load_dotenv()
    engine = get_engine(echo=echo)
    tables = sorted(Base.metadata.tables.keys())
    print(f"SQLAlchemy metadata tables before create_all: {tables}")
    logger.info("SQLAlchemy metadata tables before create_all: %s", tables)
    Base.metadata.create_all(bind=engine)
    logger.info("SQLAlchemy metadata tables after create_all: %s", sorted(Base.metadata.tables.keys()))


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for schema initialization."""
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Create DefenSync PostgreSQL tables.",
    )
    parser.add_argument(
        "--echo",
        action="store_true",
        help="Enable SQLAlchemy SQL echo output.",
    )
    args = parser.parse_args(argv)

    try:
        create_tables(echo=args.echo)
    except Exception as exc:
        print(f"Failed to initialize database schema: {exc}", file=sys.stderr)
        return 1

    print("DefenSync database schema initialized successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
