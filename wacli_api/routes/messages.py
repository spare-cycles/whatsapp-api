"""Message endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text as sa_text
from sqlalchemy.engine import Engine
from sqlmodel import Session, col, select

from wacli_api.database import get_engine, get_session
from wacli_api.db import parse_time, ts_to_iso
from wacli_api.deps import verify_api_key
from wacli_api.models import Message, MessageOut
from wacli_api.schemas import ApiResponse

router = APIRouter(dependencies=[Depends(verify_api_key)])


def _map_message(m: Message, snippet: str = "") -> MessageOut:
    return MessageOut(
        ChatJID=m.chat_jid,
        ChatName=m.chat_name or "",
        MsgID=m.msg_id,
        SenderJID=m.sender_jid or "",
        Timestamp=ts_to_iso(m.ts),
        FromMe=bool(m.from_me),
        Text=m.text or "",
        DisplayText=m.display_text or "",
        MediaType=m.media_type or "",
        Snippet=snippet,
    )


def _map_message_dict(d: dict[str, Any]) -> MessageOut:
    """Map a raw SQL result row (FTS search) to MessageOut.

    The FTS query aliases snippet(...) AS snip — mapped to the Snippet field.
    """
    return MessageOut(
        ChatJID=str(d["chat_jid"]),
        ChatName=str(d.get("chat_name") or ""),
        MsgID=str(d["msg_id"]),
        SenderJID=str(d.get("sender_jid") or ""),
        Timestamp=ts_to_iso(int(d["ts"])),
        FromMe=bool(d["from_me"]),
        Text=str(d.get("text") or ""),
        DisplayText=str(d.get("display_text") or ""),
        MediaType=str(d.get("media_type") or ""),
        Snippet=str(d.get("snip") or ""),  # query alias is "snip"
    )


@router.get("/messages")
def list_messages(
    chat: str,
    after: str | None = None,
    before: str | None = None,
    limit: int = 10000,
    session: Session = Depends(get_session),
) -> ApiResponse[dict[str, list[MessageOut]]]:
    try:
        after_ts = parse_time(after) if after else None
        before_ts = parse_time(before) if before else None
    except ValueError:
        return ApiResponse(
            success=False,
            error="invalid time format (use RFC3339 or YYYY-MM-DD)",
        )

    stmt = select(Message).where(Message.chat_jid == chat)
    if after_ts is not None:
        stmt = stmt.where(col(Message.ts) > after_ts)
    if before_ts is not None:
        stmt = stmt.where(col(Message.ts) < before_ts)
    stmt = stmt.order_by(col(Message.ts).desc()).limit(limit)

    msgs = session.exec(stmt).all()
    return ApiResponse(
        success=True,
        data={"messages": [_map_message(m) for m in msgs]},
    )


@router.get("/messages/search")
def search_messages(
    query: str,
    engine: Engine = Depends(get_engine),
) -> ApiResponse[dict[str, list[MessageOut]]]:
    sql = sa_text(
        "SELECT m.chat_jid, m.chat_name, m.msg_id, m.sender_jid, m.ts, m.from_me,"
        " m.text, m.display_text, m.media_type,"
        " snippet(messages_fts, 0, '', '', '\u2026', 20) AS snip"
        " FROM messages_fts"
        " JOIN messages m ON m.rowid = messages_fts.rowid"
        " WHERE messages_fts MATCH :q"
        " ORDER BY m.ts DESC"
    )
    with engine.connect() as conn:
        rows = conn.execute(sql, {"q": query}).mappings().all()
    return ApiResponse(
        success=True,
        data={"messages": [_map_message_dict(dict(r)) for r in rows]},
    )
