"""Message endpoints."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from wacli_api.db import get_db, parse_time, ts_to_iso
from wacli_api.deps import get_settings, verify_api_key
from wacli_api.schemas import ApiResponse
from wacli_api.settings import Settings

router = APIRouter(dependencies=[Depends(verify_api_key)])


def _map_message(row: sqlite3.Row, snippet: str = "") -> dict:  # type: ignore[type-arg]
    return {
        "ChatJID":     row["chat_jid"],
        "ChatName":    row["chat_name"] or "",
        "MsgID":       row["msg_id"],
        "SenderJID":   row["sender_jid"] or "",
        "Timestamp":   ts_to_iso(row["ts"]),
        "FromMe":      bool(row["from_me"]),
        "Text":        row["text"] or "",
        "DisplayText": row["display_text"] or "",
        "MediaType":   row["media_type"] or "",
        "Snippet":     snippet,
    }


@router.get("/messages")
def list_messages(
    chat: str,
    after: str | None = None,
    before: str | None = None,
    limit: int = 10000,
    settings: Settings = Depends(get_settings),
) -> ApiResponse:
    try:
        after_ts = parse_time(after) if after else None
        before_ts = parse_time(before) if before else None
    except ValueError:
        return ApiResponse(success=False, error="invalid time format (use RFC3339 or YYYY-MM-DD)")

    query = (
        "SELECT chat_jid, chat_name, msg_id, sender_jid, ts, from_me, text, display_text, media_type"
        " FROM messages WHERE chat_jid = ?"
    )
    args: list[object] = [chat]
    if after_ts is not None:
        query += " AND ts > ?"
        args.append(after_ts)
    if before_ts is not None:
        query += " AND ts < ?"
        args.append(before_ts)
    query += " ORDER BY ts DESC LIMIT ?"
    args.append(limit)

    with get_db(settings.store_db) as conn:
        rows = conn.execute(query, args).fetchall()

    return ApiResponse(success=True, data={"messages": [_map_message(r) for r in rows]})


@router.get("/messages/search")
def search_messages(
    query: str,
    settings: Settings = Depends(get_settings),
) -> ApiResponse:
    sql = (
        "SELECT m.chat_jid, m.chat_name, m.msg_id, m.sender_jid, m.ts, m.from_me,"
        " m.text, m.display_text, m.media_type,"
        " snippet(messages_fts, 0, '', '', '\u2026', 20) AS snip"
        " FROM messages_fts"
        " JOIN messages m ON m.rowid = messages_fts.rowid"
        " WHERE messages_fts MATCH ?"
        " ORDER BY m.ts DESC"
    )
    with get_db(settings.store_db) as conn:
        rows = conn.execute(sql, [query]).fetchall()

    return ApiResponse(
        success=True,
        data={"messages": [_map_message(r, r["snip"] or "") for r in rows]},
    )
