"""Contact endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text as sa_text
from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from wacli_api.database import get_engine, get_session
from wacli_api.db import ts_to_iso
from wacli_api.deps import verify_api_key
from wacli_api.models import ContactOut, ContactTag
from wacli_api.schemas import ApiResponse

router = APIRouter(dependencies=[Depends(verify_api_key)])

# Name resolution priority matches wacli's GetContact SQL exactly:
# COALESCE(NULLIF(full_name,''), NULLIF(push_name,''), NULLIF(business_name,''),
#          NULLIF(first_name,''), '')
_CONTACT_SQL = sa_text(
    "SELECT c.jid,"
    " COALESCE(c.phone, '') AS phone,"
    " COALESCE(NULLIF(a.alias, ''), '') AS alias,"
    " COALESCE(NULLIF(c.full_name, ''), NULLIF(c.push_name, ''),"
    "          NULLIF(c.business_name, ''), NULLIF(c.first_name, ''), '') AS name,"
    " c.updated_at"
    " FROM contacts c"
    " LEFT JOIN contact_aliases a ON a.jid = c.jid"
    " WHERE c.jid = :jid"
)

_CONTACT_SEARCH_SQL = sa_text(
    "SELECT c.jid,"
    " COALESCE(c.phone, '') AS phone,"
    " COALESCE(NULLIF(a.alias, ''), '') AS alias,"
    " COALESCE(NULLIF(c.full_name, ''), NULLIF(c.push_name, ''),"
    "          NULLIF(c.business_name, ''), NULLIF(c.first_name, ''), '') AS name,"
    " c.updated_at"
    " FROM contacts c"
    " LEFT JOIN contact_aliases a ON a.jid = c.jid"
    " WHERE c.full_name     LIKE :pattern"
    "    OR c.push_name     LIKE :pattern"
    "    OR c.first_name    LIKE :pattern"
    "    OR c.business_name LIKE :pattern"
    "    OR c.phone         LIKE :pattern"
    "    OR a.alias         LIKE :pattern"
)


def _phone_from_jid(jid: str) -> str:
    """Extract a phone number from a JID.

    Example: '33782300839@s.whatsapp.net' -> '+33782300839'.
    Returns the original JID if no phone number can be extracted.
    """
    local = jid.split("@")[0].split(":")[0]
    if local.isdigit():
        return f"+{local}"
    return jid


def _build_contact_out(row: dict[str, Any], jid: str, tags: list[str]) -> ContactOut:
    name = str(row.get("name") or "")
    return ContactOut(
        JID=jid,
        Phone=str(row.get("phone") or ""),
        Alias=str(row.get("alias") or ""),
        Name=name,
        Tags=tags,
        UpdatedAt=ts_to_iso(int(row.get("updated_at") or 0)),
        display_name=name or _phone_from_jid(jid),
    )


def _fetch_tags(session: Session, jid: str) -> list[str]:
    return [
        t.tag
        for t in session.exec(select(ContactTag).where(ContactTag.jid == jid)).all()
    ]


@router.get("/contacts")
def show_contact(
    jid: str,
    session: Session = Depends(get_session),
    engine: Engine = Depends(get_engine),
) -> ApiResponse[ContactOut]:
    with engine.connect() as conn:
        row = conn.execute(_CONTACT_SQL, {"jid": jid}).mappings().first()
    if row is None:
        return ApiResponse(
            success=True,
            data=ContactOut(
                JID=jid,
                Phone="",
                Alias="",
                Name="",
                Tags=[],
                UpdatedAt="0001-01-01T00:00:00Z",
                display_name=_phone_from_jid(jid),
            ),
        )
    tags = _fetch_tags(session, jid)
    return ApiResponse(success=True, data=_build_contact_out(dict(row), jid, tags))


@router.get("/contacts/search")
def search_contacts(
    query: str,
    session: Session = Depends(get_session),
    engine: Engine = Depends(get_engine),
) -> ApiResponse[list[ContactOut]]:
    with engine.connect() as conn:
        rows = (
            conn.execute(_CONTACT_SEARCH_SQL, {"pattern": f"%{query}%"})
            .mappings()
            .all()
        )
    results: list[ContactOut] = []
    for row in rows:
        jid = str(row["jid"])
        tags = _fetch_tags(session, jid)
        results.append(_build_contact_out(dict(row), jid, tags))
    return ApiResponse(success=True, data=results)
