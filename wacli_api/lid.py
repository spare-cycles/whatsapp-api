"""LID-to-phone JID resolution using whatsmeow's session database."""

from __future__ import annotations

import logging
import sqlite3

logger = logging.getLogger(__name__)

_lid_map: dict[str, str] = {}


def load_lid_map(db_path: str) -> dict[str, str]:
    """Read the whatsmeow_lid_map table from wacli's session SQLite DB.

    Returns a dict mapping bare LID numbers to phone numbers.
    Returns an empty dict if the file is missing, locked, or unreadable.
    """
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        rows = conn.execute("SELECT lid, pn FROM whatsmeow_lid_map").fetchall()
        conn.close()
        mapping = {str(row[0]): str(row[1]) for row in rows}
        logger.info("Loaded %d LID-to-phone mappings from %s", len(mapping), db_path)
        return mapping
    except (sqlite3.OperationalError, sqlite3.DatabaseError) as exc:
        logger.warning("Could not read LID map from %s: %s", db_path, exc)
        return {}


def reload(db_path: str) -> None:
    """Reload the LID map from disk."""
    global _lid_map  # noqa: PLW0603
    _lid_map = load_lid_map(db_path)


def get_map() -> dict[str, str]:
    """Return the current LID map."""
    return dict(_lid_map)


def normalize_jid(raw_jid: str) -> str:
    """Normalize a WhatsApp JID: convert @lid to @s.whatsapp.net if mapping exists."""
    if not raw_jid.endswith("@lid"):
        return raw_jid
    bare = raw_jid[:-4].split(":")[0]
    phone = _lid_map.get(bare)
    if phone is None:
        return raw_jid
    return f"{phone}@s.whatsapp.net"
