"""Send message endpoints."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import redis as _redis
from fastapi import APIRouter, Depends, UploadFile

from wacli_api.deps import get_redis, get_settings, verify_api_key
from wacli_api.schemas import ApiResponse, SendTextRequest
from wacli_api.settings import Settings

router = APIRouter(dependencies=[Depends(verify_api_key)])

_QUEUE = "wacli:send"


@router.post("/send/text")
def send_text(
    req: SendTextRequest,
    settings: Settings = Depends(get_settings),
    r: _redis.Redis = Depends(get_redis),  # type: ignore[type-arg]
) -> ApiResponse:
    job_id = str(uuid.uuid4())
    r.lpush(_QUEUE, json.dumps({"id": job_id, "type": "text", "to": req.to, "body": req.body}))
    reply = r.blpop(f"wacli:send:reply:{job_id}", timeout=settings.timeout)
    if reply is None:
        return ApiResponse(success=False, error="send timed out")
    return ApiResponse(**json.loads(reply[1]))


@router.post("/send/file")
def send_file(
    to: str,
    file: UploadFile,
    settings: Settings = Depends(get_settings),
    r: _redis.Redis = Depends(get_redis),  # type: ignore[type-arg]
) -> ApiResponse:
    suffix = Path(file.filename or "upload").suffix
    job_id = str(uuid.uuid4())
    upload_path = f"/uploads/{job_id}{suffix}"
    try:
        Path(upload_path).write_bytes(file.file.read())
        r.lpush(
            _QUEUE,
            json.dumps({"id": job_id, "type": "file", "to": to, "file_path": upload_path}),
        )
        reply = r.blpop(f"wacli:send:reply:{job_id}", timeout=settings.timeout)
        if reply is None:
            return ApiResponse(success=False, error="send timed out")
        return ApiResponse(**json.loads(reply[1]))
    except _redis.RedisError as exc:
        return ApiResponse(success=False, error=str(exc))
    finally:
        # Safe to call even if the worker already deleted the file
        Path(upload_path).unlink(missing_ok=True)
