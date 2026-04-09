"""Test fixtures."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from wacli_api.main import app
from wacli_api.settings import Settings


@pytest.fixture
def client() -> Iterator[TestClient]:
    # Override settings for tests: no API key required
    app.state.settings = Settings(api_key=None, session_db=":memory:")
    with TestClient(app) as c:
        yield c


@pytest.fixture
def authed_client() -> Iterator[TestClient]:
    app.state.settings = Settings(api_key="test-key", session_db=":memory:")
    with TestClient(app) as c:
        yield c
