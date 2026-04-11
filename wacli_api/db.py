"""Direct read-only SQLite access for wacli.db."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone


@contextmanager
def get_db(path: str) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=5000")
    try:
        yield conn
    finally:
        conn.close()


def parse_time(s: str) -> int:
    """Parse RFC3339 or YYYY-MM-DD string → Unix timestamp (int).

    Raises ValueError on unrecognised format.
    """
    s = s.strip()
    try:
        return int(datetime.fromisoformat(s).timestamp())
    except ValueError:
        pass
    return int(datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def ts_to_iso(unix: int) -> str:
    """Convert Unix int → RFC3339 string, matching wacli's Go time.Time serialisation."""
    if not unix:
        return "0001-01-01T00:00:00Z"
    return datetime.fromtimestamp(unix, tz=timezone.utc).isoformat()
