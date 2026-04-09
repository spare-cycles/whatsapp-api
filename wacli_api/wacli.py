"""Subprocess wrapper for the wacli CLI."""

from __future__ import annotations

import json
import logging
import subprocess
from typing import Any, cast

logger = logging.getLogger(__name__)

type JsonDict = dict[str, Any]


def run_wacli(args: list[str], *, timeout: int = 60) -> JsonDict:
    """Run a wacli command with --json and return parsed output."""
    cmd = ["wacli", *args, "--json"]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False, timeout=timeout
        )
    except subprocess.TimeoutExpired as exc:
        msg = f"wacli timed out after {timeout}s: {args}"
        logger.error(msg)
        raise RuntimeError(msg) from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()
        msg = f"wacli failed (exit {result.returncode}): {stderr}"
        logger.error("wacli command %s failed: %s", args, stderr)
        raise RuntimeError(msg)

    parsed: JsonDict = json.loads(result.stdout)
    if not parsed.get("success"):
        error = parsed.get("error", "unknown error")
        msg = f"wacli error: {error}"
        logger.error("wacli command %s returned error: %s", args, error)
        raise RuntimeError(msg)

    return parsed


def extract_data_list(data: JsonDict) -> list[JsonDict]:
    """Extract the data field when it's a flat list (e.g. chats)."""
    raw: Any = data.get("data")
    if isinstance(raw, list):
        return raw  # type: ignore[no-any-return]
    return []


def extract_nested_list(data: JsonDict, *keys: str) -> list[JsonDict]:
    """Navigate nested JSON keys and extract a list, or return []."""
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return []
        current = cast(Any, current.get(key))
    if not isinstance(current, list):
        return []
    return current  # type: ignore[no-any-return]
