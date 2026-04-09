"""Tests for the health endpoint."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient


class TestHealth:
    def test_healthy(self, client: TestClient) -> None:
        payload = {"success": True, "data": {"authenticated": True}}
        with patch("wacli_api.routes.health.run_wacli", return_value=payload):
            resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["authenticated"] is True

    def test_unhealthy(self, client: TestClient) -> None:
        with patch("wacli_api.routes.health.run_wacli", side_effect=RuntimeError("not authed")):
            resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False

    def test_no_auth_required(self, authed_client: TestClient) -> None:
        """Health endpoint must work without API key even when auth is configured."""
        payload = {"success": True, "data": {"authenticated": True}}
        with patch("wacli_api.routes.health.run_wacli", return_value=payload):
            resp = authed_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_other_endpoint_requires_auth(self, authed_client: TestClient) -> None:
        """Non-health endpoints must require API key."""
        resp = authed_client.get("/chats")
        assert resp.status_code == 401
