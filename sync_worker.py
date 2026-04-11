"""Redis consumer — runs wacli send commands on behalf of the API container."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from pathlib import Path

import redis

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("sync_worker")

_QUEUE = "wacli:send"
_REPLY_TTL = 300  # seconds; orphaned reply keys auto-expire


def _make_client() -> redis.Redis:  # type: ignore[type-arg]
    return redis.Redis.from_url(
        os.environ.get("WACLI_REDIS_URL", "redis://redis:6379"),
        decode_responses=True,
    )


def _run_send(job: dict) -> dict:  # type: ignore[type-arg]
    job_type = job.get("type")
    if job_type == "text":
        cmd = ["wacli", "send", "text", "--to", job["to"], "--message", job["body"], "--json"]
    elif job_type == "file":
        cmd = ["wacli", "send", "file", "--to", job["to"], "--file", job["file_path"], "--json"]
    else:
        return {"success": False, "error": f"unknown job type: {job_type!r}", "data": None}

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return {"success": False, "error": result.stderr.strip(), "data": None}
        parsed = json.loads(result.stdout)
        return {
            "success": parsed.get("success", False),
            "data": parsed.get("data"),
            "error": parsed.get("error"),
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "wacli send timed out", "data": None}
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}
    finally:
        if job_type == "file":
            Path(job.get("file_path", "")).unlink(missing_ok=True)


log.info("sync_worker ready, listening on %s", _QUEUE)
r = _make_client()
while True:
    try:
        item = r.brpop(_QUEUE, timeout=0)
        if item is None:
            continue
        job = json.loads(item[1])
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
