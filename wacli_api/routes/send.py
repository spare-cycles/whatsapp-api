"""Send message endpoints."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile

from wacli_api.deps import get_redis, get_settings, verify_api_key
from wacli_api.redis_types import RedisClient
from wacli_api.schemas import ApiResponse, SendTextRequest
from wacli_api.settings import Settings

router = APIRouter(dependencies=[Depends(verify_api_key)])

_QUEUE = "wacli:send"


@router.post("/send/text")
def send_text(
    req: SendTextRequest,
    settings: Settings = Depends(get_settings),
    r: RedisClient = Depends(get_redis),
) -> ApiResponse[object]:
    job_id = str(uuid.uuid4())
    r.lpush(
        _QUEUE,
        json.dumps({"id": job_id, "type": "text", "to": req.to, "body": req.body}),
    )
    raw = r.blpop(f"wacli:send:reply:{job_id}", timeout=settings.timeout)
    if raw is None:
        return ApiResponse(success=False, error="send timed out")
    payload = raw[1]
    return ApiResponse[object].model_validate(json.loads(payload))


@router.post("/send/file")
def send_file(
    to: str,
    file: UploadFile,
    settings: Settings = Depends(get_settings),
    r: RedisClient = Depends(get_redis),
) -> ApiResponse[object]:
    suffix = Path(file.filename or "upload").suffix
    job_id = str(uuid.uuid4())
    upload_path = f"/uploads/{job_id}{suffix}"
    try:
        Path(upload_path).write_bytes(file.file.read())
        r.lpush(
            _QUEUE,
            json.dumps(
                {
                    "id": job_id,
                    "type": "file",
                    "to": to,
                    "file_path": upload_path,
                }
            ),
        )
        raw = r.blpop(f"wacli:send:reply:{job_id}", timeout=settings.timeout)
        if raw is None:
            return ApiResponse(success=False, error="send timed out")
        payload = raw[1]
        return ApiResponse[object].model_validate(json.loads(payload))
    except Exception as exc:
        return ApiResponse(success=False, error=str(exc))
    finally:
        # Safe to call even if the worker already deleted the file
        Path(upload_path).unlink(missing_ok=True)
