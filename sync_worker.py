"""Redis consumer — runs wacli send commands on behalf of the API container."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Protocol, cast
from urllib.parse import urlparse

import redis

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("sync_worker")

_QUEUE = "wacli:send"
_REPLY_TTL = 300  # seconds; orphaned reply keys auto-expire


class _SyncRedis(Protocol):
    """Subset of redis.Redis used by the worker, with correct sync return types."""

    def brpop(self, keys: str, timeout: int | float = 0) -> list[str] | None: ...

    def lpush(self, name: str, *values: str | bytes) -> int: ...

    def expire(self, name: str, time: int) -> bool: ...


def _make_client() -> _SyncRedis:
    url = os.environ.get("WACLI_REDIS_URL", "redis://redis:6379")
    parsed = urlparse(url)
    return cast(
        _SyncRedis,
        redis.Redis(
            host=parsed.hostname or "localhost",
            port=parsed.port or 6379,
            db=int((parsed.path or "").lstrip("/") or "0"),
            password=parsed.password,
            username=parsed.username or None,
            decode_responses=True,
        ),
    )


def _run_send(job: dict[str, Any]) -> dict[str, Any]:
    job_type: str | None = job.get("type")
    if job_type == "text":
        cmd = [
            "wacli",
            "send",
            "text",
            "--to",
            str(job["to"]),
            "--message",
            str(job["body"]),
            "--json",
        ]
    elif job_type == "file":
        cmd = [
            "wacli",
            "send",
            "file",
            "--to",
            str(job["to"]),
            "--file",
            str(job["file_path"]),
            "--json",
        ]
    else:
        return {
            "success": False,
            "error": f"unknown job type: {job_type!r}",
            "data": None,
        }

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return {"success": False, "error": result.stderr.strip(), "data": None}
        parsed_result: dict[str, Any] = json.loads(result.stdout)
        return {
            "success": parsed_result.get("success", False),
            "data": parsed_result.get("data"),
            "error": parsed_result.get("error"),
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "wacli send timed out", "data": None}
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}
    finally:
        if job_type == "file":
            Path(str(job.get("file_path", ""))).unlink(missing_ok=True)


log.info("sync_worker ready, listening on %s", _QUEUE)
r = _make_client()
while True:
    try:
        item = r.brpop(_QUEUE, timeout=0)
        if item is None:
            continue
        payload = item[1]
        job: dict[str, Any] = json.loads(payload)
        log.info("processing job %s type=%s", job.get("id"), job.get("type"))
        response = _run_send(job)
        reply_key = f"wacli:send:reply:{job['id']}"
        r.lpush(reply_key, json.dumps(response))
        r.expire(reply_key, _REPLY_TTL)
    except redis.ConnectionError as exc:
        log.error("Redis connection lost: %s — reconnecting in 5s", exc)
        time.sleep(5)
        r = _make_client()
    except Exception as exc:
        log.error("Unexpected error: %s", exc)
        time.sleep(1)
