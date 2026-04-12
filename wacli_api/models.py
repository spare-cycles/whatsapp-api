"""SQLModel DB table models (read-only) and Pydantic response models."""

from __future__ import annotations

from pydantic import BaseModel
from sqlmodel import Field, SQLModel

# ── DB table models ───────────────────────────────────────────────────────────
# These map to existing tables in wacli.db (read-only).
# Never call SQLModel.metadata.create_all() in production — tables already exist.
# __tablename__ must be explicit: SQLModel defaults to lowercase class name,
# which differs from the actual table names (e.g. Group → "group" not "groups").


class Chat(SQLModel, table=True):
    __tablename__ = "chats"  # type: ignore[assignment]

    jid: str = Field(primary_key=True)
    kind: str
    name: str | None = None
    last_message_ts: int | None = None


class Group(SQLModel, table=True):
    __tablename__ = "groups"  # type: ignore[assignment]

    jid: str = Field(primary_key=True)
    name: str | None = None
    owner_jid: str | None = None
    created_ts: int | None = None
    updated_at: int | None = None


class GroupParticipant(SQLModel, table=True):
    __tablename__ = "group_participants"  # type: ignore[assignment]

    group_jid: str = Field(primary_key=True)
    user_jid: str = Field(primary_key=True)
    role: str


class Message(SQLModel, table=True):
    __tablename__ = "messages"  # type: ignore[assignment]

    chat_jid: str = Field(primary_key=True)
    msg_id: str = Field(primary_key=True)
    chat_name: str | None = None
    sender_jid: str | None = None
    ts: int
    from_me: int  # SQLite INTEGER (0/1); convert to bool in response
    text: str | None = None
    display_text: str | None = None
    media_type: str | None = None


class Contact(SQLModel, table=True):
    __tablename__ = "contacts"  # type: ignore[assignment]

    jid: str = Field(primary_key=True)
    phone: str | None = None
    full_name: str | None = None
    push_name: str | None = None
    business_name: str | None = None
    first_name: str | None = None
    updated_at: int | None = None


class ContactAlias(SQLModel, table=True):
    __tablename__ = "contact_aliases"  # type: ignore[assignment]

    jid: str = Field(primary_key=True)
    alias: str


class ContactTag(SQLModel, table=True):
    __tablename__ = "contact_tags"  # type: ignore[assignment]

    jid: str = Field(primary_key=True)
    tag: str = Field(primary_key=True)


# ── Pydantic response models ──────────────────────────────────────────────────
# Field names match the existing API contract (Go/wacli conventions).


class ChatOut(BaseModel):
    JID: str
    Kind: str
    Name: str
    LastMessageTS: str


class ParticipantOut(BaseModel):
    UserJID: str
    Role: str


class GroupOut(BaseModel):
    JID: str
    Name: str
    OwnerJID: str
    CreatedAt: str
    UpdatedAt: str


class GroupDetailOut(GroupOut):
    Participants: list[ParticipantOut] = []


class MessageOut(BaseModel):
    ChatJID: str
    ChatName: str
    MsgID: str
    SenderJID: str
    Timestamp: str
    FromMe: bool
    Text: str
    DisplayText: str
    MediaType: str
    Snippet: str = ""


class ContactOut(BaseModel):
    JID: str
    Phone: str
    Alias: str
    Name: str
    Tags: list[str]
    UpdatedAt: str
    display_name: str
