"""SQLAlchemy engine factory and session/engine dependencies for FastAPI."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine


def make_engine(db_path: str) -> Engine:
    """Create a read-only SQLAlchemy engine for the given SQLite path."""
    return create_engine(
        f"sqlite:///file:{db_path}?mode=ro&uri=true",
        connect_args={"check_same_thread": False},
    )


def get_engine(request: Request) -> Engine:
    """FastAPI dependency: returns the SQLAlchemy engine from app.state."""
    return request.app.state.engine  # type: ignore[no-any-return]


def get_session(request: Request) -> Iterator[Session]:
    """FastAPI dependency: yields a SQLModel Session from app.state.engine."""
    with Session(request.app.state.engine) as session:
        yield session
