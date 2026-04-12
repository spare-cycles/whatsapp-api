"""Tests for the health endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestHealth:
    def test_healthy(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "db" in body["data"]
        assert "redis" in body["data"]

    def test_no_auth_required(self, authed_client: TestClient) -> None:
        """Health endpoint must work without API key even when auth is configured."""
        resp = authed_client.get("/health")
        assert resp.status_code == 200

    def test_other_endpoint_requires_auth(self, authed_client: TestClient) -> None:
        """Non-health endpoints must require API key."""
        resp = authed_client.get("/chats")
        assert resp.status_code == 401
