#!/usr/bin/env python3
"""Drop and recreate all DefenSync tables (use when schema is out of date)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv()

from backend.database.connection import get_engine
from backend.database.models import Base


def reset() -> None:
    engine = get_engine()
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating fresh schema...")
    Base.metadata.create_all(bind=engine)
    print("Database reset complete.")


if __name__ == "__main__":
    confirm = input("This will DELETE all data. Type YES to continue: ")
    if confirm.strip().upper() != "YES":
        print("Aborted.")
        raise SystemExit(0)
    try:
        reset()
    except Exception as exc:
        print(f"Reset failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
