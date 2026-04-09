"""Tests for the wacli subprocess wrapper."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from wacli_api.wacli import extract_data_list, extract_nested_list, run_wacli

_SUBPROCESS = "wacli_api.wacli.subprocess.run"


def _mock_result(stdout: str, returncode: int = 0, stderr: str = "") -> object:
    class R:
        pass

    r = R()
    r.stdout = stdout  # type: ignore[attr-defined]
    r.stderr = stderr  # type: ignore[attr-defined]
    r.returncode = returncode  # type: ignore[attr-defined]
    return r


class TestRunWacli:
    def test_success(self) -> None:
        payload = {"success": True, "data": {"ok": True}}
        with patch(_SUBPROCESS, return_value=_mock_result(json.dumps(payload))) as mock:
            result = run_wacli(["auth", "status"])
        assert result == payload
        mock.assert_called_once()
        assert mock.call_args[0][0] == ["wacli", "auth", "status", "--json"]

    def test_nonzero_exit(self) -> None:
        with patch(_SUBPROCESS, return_value=_mock_result("", 1, "bad")):
            with pytest.raises(RuntimeError, match="wacli failed"):
                run_wacli(["auth", "status"])

    def test_success_false(self) -> None:
        payload = {"success": False, "error": "not authed"}
        with patch(_SUBPROCESS, return_value=_mock_result(json.dumps(payload))):
            with pytest.raises(RuntimeError, match="wacli error"):
                run_wacli(["auth", "status"])


class TestExtractors:
    def test_data_list(self) -> None:
        assert extract_data_list({"data": [{"a": 1}]}) == [{"a": 1}]

    def test_data_list_not_list(self) -> None:
        assert extract_data_list({"data": "nope"}) == []

    def test_nested_list(self) -> None:
        data = {"data": {"messages": [{"id": 1}]}}
        assert extract_nested_list(data, "data", "messages") == [{"id": 1}]

    def test_nested_list_missing(self) -> None:
        assert extract_nested_list({"data": {}}, "data", "messages") == []
