"""Time parsing and formatting utilities for wacli timestamps."""

from __future__ import annotations

from datetime import UTC, datetime


def parse_time(s: str) -> int:
    """Parse RFC3339 or YYYY-MM-DD string → Unix timestamp (int).

    Raises ValueError on unrecognised format.
    """
    s = s.strip()
    try:
        return int(datetime.fromisoformat(s).timestamp())
    except ValueError:
        pass
    return int(datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=UTC).timestamp())


def ts_to_iso(unix: int) -> str:
    """Convert Unix timestamp → RFC3339 string (matches wacli's Go time.Time format)."""
    if not unix:
        return "0001-01-01T00:00:00Z"
    return datetime.fromtimestamp(unix, tz=UTC).isoformat()
