"""Chat endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, col, select

from wacli_api.database import get_session
from wacli_api.db import ts_to_iso
from wacli_api.deps import verify_api_key
from wacli_api.models import Chat, ChatOut
from wacli_api.schemas import ApiResponse

router = APIRouter(dependencies=[Depends(verify_api_key)])


def _map_chat(c: Chat) -> ChatOut:
    return ChatOut(
        JID=c.jid,
        Kind=c.kind,
        Name=c.name or "",
        LastMessageTS=ts_to_iso(c.last_message_ts or 0),
    )


@router.get("/chats")
def list_chats(
    limit: int = 10000,
    session: Session = Depends(get_session),
) -> ApiResponse[list[ChatOut]]:
    chats = session.exec(
        select(Chat).order_by(col(Chat.last_message_ts).desc()).limit(limit)
    ).all()
    return ApiResponse(success=True, data=[_map_chat(c) for c in chats])


@router.get("/chats/show")
def show_chat(
    jid: str,
    session: Session = Depends(get_session),
) -> ApiResponse[ChatOut]:
    chat = session.exec(select(Chat).where(Chat.jid == jid)).first()
    if chat is None:
        return ApiResponse(success=False, error="chat not found")
    return ApiResponse(success=True, data=_map_chat(chat))
