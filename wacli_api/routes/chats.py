"""Chat endpoints."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from wacli_api.db import get_db, ts_to_iso
from wacli_api.deps import get_settings, verify_api_key
from wacli_api.schemas import ApiResponse
from wacli_api.settings import Settings

router = APIRouter(dependencies=[Depends(verify_api_key)])


def _map_chat(row: sqlite3.Row) -> dict:  # type: ignore[type-arg]
    return {
        "JID":           row["jid"],
        "Kind":          row["kind"],
        "Name":          row["name"] or "",
        "LastMessageTS": ts_to_iso(row["last_message_ts"] or 0),
    }


@router.get("/chats")
def list_chats(
    limit: int = 10000,
    settings: Settings = Depends(get_settings),
) -> ApiResponse:
    with get_db(settings.store_db) as conn:
        rows = conn.execute(
            "SELECT jid, kind, name, last_message_ts FROM chats"
            " ORDER BY last_message_ts DESC LIMIT ?",
            [limit],
        ).fetchall()
    return ApiResponse(success=True, data=[_map_chat(r) for r in rows])


@router.get("/chats/show")
def show_chat(
    jid: str,
    settings: Settings = Depends(get_settings),
) -> ApiResponse:
    with get_db(settings.store_db) as conn:
        row = conn.execute(
            "SELECT jid, kind, name, last_message_ts FROM chats WHERE jid = ?",
            [jid],
        ).fetchone()
    if row is None:
        return ApiResponse(success=False, error="chat not found")
    return ApiResponse(success=True, data=_map_chat(row))
