"""Group endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from wacli_api.database import get_session
from wacli_api.db import ts_to_iso
from wacli_api.deps import verify_api_key
from wacli_api.models import (
    Group,
    GroupDetailOut,
    GroupOut,
    GroupParticipant,
    ParticipantOut,
)
from wacli_api.schemas import ApiResponse

router = APIRouter(dependencies=[Depends(verify_api_key)])


def _map_group(g: Group) -> GroupOut:
    return GroupOut(
        JID=g.jid,
        Name=g.name or "",
        OwnerJID=g.owner_jid or "",
        CreatedAt=ts_to_iso(g.created_ts or 0),
        UpdatedAt=ts_to_iso(g.updated_at or 0),
    )


@router.get("/groups")
def list_groups(
    limit: int = 10000,
    session: Session = Depends(get_session),
) -> ApiResponse[list[GroupOut]]:
    groups = session.exec(select(Group).limit(limit)).all()
    return ApiResponse(success=True, data=[_map_group(g) for g in groups])


@router.get("/groups/show")
def show_group(
    jid: str,
    session: Session = Depends(get_session),
) -> ApiResponse[GroupDetailOut]:
    group = session.exec(select(Group).where(Group.jid == jid)).first()
    if group is None:
        return ApiResponse(success=False, error="group not found")
    participants = session.exec(
        select(GroupParticipant).where(GroupParticipant.group_jid == jid)
    ).all()
    return ApiResponse(
        success=True,
        data=GroupDetailOut(
            **_map_group(group).model_dump(),
            Participants=[
                ParticipantOut(UserJID=p.user_jid, Role=p.role) for p in participants
            ],
        ),
    )
