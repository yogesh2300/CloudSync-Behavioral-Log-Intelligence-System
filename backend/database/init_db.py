"""Initialize CloudSync PostgreSQL schema."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from dotenv import load_dotenv

from backend.database.connection import get_engine
from backend.database.models import Base


def create_tables(*, echo: bool = False) -> None:
    """Create all database tables defined on the declarative Base."""
    load_dotenv()
    engine = get_engine(echo=echo)
    Base.metadata.create_all(bind=engine)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for schema initialization."""
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Create CloudSync PostgreSQL tables.",
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

    print("CloudSync database schema initialized successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
