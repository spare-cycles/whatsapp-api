"""Contact endpoints."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from wacli_api.db import get_db, ts_to_iso
from wacli_api.deps import get_settings, verify_api_key
from wacli_api.schemas import ApiResponse
from wacli_api.settings import Settings

router = APIRouter(dependencies=[Depends(verify_api_key)])

# Name resolution priority matches wacli's GetContact SQL exactly:
# COALESCE(NULLIF(full_name,''), NULLIF(push_name,''), NULLIF(business_name,''), NULLIF(first_name,''), '')
_CONTACT_SELECT = """
    SELECT c.jid,
           COALESCE(c.phone, ''),
           COALESCE(NULLIF(a.alias, ''), ''),
           COALESCE(NULLIF(c.full_name, ''), NULLIF(c.push_name, ''),
                    NULLIF(c.business_name, ''), NULLIF(c.first_name, ''), ''),
           c.updated_at
    FROM contacts c
    LEFT JOIN contact_aliases a ON a.jid = c.jid
"""


def _phone_from_jid(jid: str) -> str:
    """Extract a phone number from a JID.

    Example: '33782300839@s.whatsapp.net' -> '+33782300839'.
    Returns the original JID if no phone number can be extracted.
    """
    local = jid.split("@")[0].split(":")[0]
    if local.isdigit():
        return f"+{local}"
    return jid


def _fetch_tags(conn: sqlite3.Connection, jid: str) -> list[str]:
    return [r[0] for r in conn.execute("SELECT tag FROM contact_tags WHERE jid = ?", [jid])]


def _map_contact(row: tuple, tags: list[str]) -> dict:  # type: ignore[type-arg]
    return {
        "JID":       row[0],
        "Phone":     row[1],
        "Alias":     row[2],
        "Name":      row[3],
        "Tags":      tags,
        "UpdatedAt": ts_to_iso(row[4] or 0),
    }


@router.get("/contacts")
def show_contact(
    jid: str,
    settings: Settings = Depends(get_settings),
) -> ApiResponse:
    with get_db(settings.store_db) as conn:
        row = conn.execute(_CONTACT_SELECT + "WHERE c.jid = ?", [jid]).fetchone()
        if row is None:
            return ApiResponse(
                success=True,
                data={"JID": jid, "display_name": _phone_from_jid(jid)},
            )
        tags = _fetch_tags(conn, jid)

    data = _map_contact(row, tags)
    data["display_name"] = data["Name"] or _phone_from_jid(jid)
    return ApiResponse(success=True, data=data)


@router.get("/contacts/search")
def search_contacts(
    query: str,
    settings: Settings = Depends(get_settings),
) -> ApiResponse:
    pattern = f"%{query}%"
    sql = (
        _CONTACT_SELECT
        + "WHERE c.full_name    LIKE ?"
        + "   OR c.push_name    LIKE ?"
        + "   OR c.first_name   LIKE ?"
        + "   OR c.business_name LIKE ?"
        + "   OR c.phone        LIKE ?"
        + "   OR a.alias        LIKE ?"
    )
    with get_db(settings.store_db) as conn:
        rows = conn.execute(sql, [pattern] * 6).fetchall()
        results = [_map_contact(r, _fetch_tags(conn, r[0])) for r in rows]
    return ApiResponse(success=True, data=results)
