"""Group endpoints."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from wacli_api.db import get_db, ts_to_iso
from wacli_api.deps import get_settings, verify_api_key
from wacli_api.schemas import ApiResponse
from wacli_api.settings import Settings

router = APIRouter(dependencies=[Depends(verify_api_key)])


def _map_group(row: sqlite3.Row) -> dict:  # type: ignore[type-arg]
    return {
        "JID":       row["jid"],
        "Name":      row["name"] or "",
        "OwnerJID":  row["owner_jid"] or "",
        "CreatedAt": ts_to_iso(row["created_ts"] or 0),
        "UpdatedAt": ts_to_iso(row["updated_at"] or 0),
    }


@router.get("/groups")
def list_groups(
    limit: int = 10000,
    settings: Settings = Depends(get_settings),
) -> ApiResponse:
    with get_db(settings.store_db) as conn:
        rows = conn.execute(
            "SELECT jid, name, owner_jid, created_ts, updated_at FROM groups LIMIT ?",
            [limit],
        ).fetchall()
    return ApiResponse(success=True, data=[_map_group(r) for r in rows])


@router.get("/groups/show")
def show_group(
    jid: str,
    settings: Settings = Depends(get_settings),
) -> ApiResponse:
    with get_db(settings.store_db) as conn:
        row = conn.execute(
            "SELECT jid, name, owner_jid, created_ts, updated_at FROM groups WHERE jid = ?",
            [jid],
        ).fetchone()
        if row is None:
            return ApiResponse(success=False, error="group not found")
        participants = [
            {"UserJID": r["user_jid"], "Role": r["role"]}
            for r in conn.execute(
                "SELECT user_jid, role FROM group_participants WHERE group_jid = ?",
                [jid],
            ).fetchall()
        ]
    data = {**_map_group(row), "Participants": participants}
    return ApiResponse(success=True, data=data)
