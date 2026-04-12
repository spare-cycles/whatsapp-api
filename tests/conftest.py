"""Test fixtures."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from wacli_api.database import get_session
from wacli_api.main import app
from wacli_api.settings import Settings

# Single module-level in-memory engine shared across all tests.
# StaticPool ensures all connections use the same in-memory DB (tables persist).
_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SQLModel.metadata.create_all(_test_engine)  # run once at module import


def _override_get_session() -> Iterator[Session]:
    with Session(_test_engine) as session:
        yield session


def _make_client(api_key: str | None) -> TestClient:
    """Build a TestClient without triggering the lifespan.

    Using 'with TestClient(app)' would start the lifespan, overwriting app.state.
    """
    app.dependency_overrides[get_session] = _override_get_session
    app.state.settings = Settings(api_key=api_key, session_db=":memory:")
    app.state.engine = _test_engine
    app.state.redis = MagicMock()
    return TestClient(app)  # no 'with' — skips lifespan startup/shutdown


@pytest.fixture
def client() -> Iterator[TestClient]:
    c = _make_client(api_key=None)
    yield c
    app.dependency_overrides.clear()


@pytest.fixture
def authed_client() -> Iterator[TestClient]:
    c = _make_client(api_key="test-key")
    yield c
    app.dependency_overrides.clear()
