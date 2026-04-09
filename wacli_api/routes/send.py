"""Send message endpoints."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile

from wacli_api.deps import get_settings, verify_api_key
from wacli_api.schemas import ApiResponse, SendTextRequest
from wacli_api.settings import Settings
from wacli_api.wacli import run_wacli

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.post("/send/text")
def send_text(
    req: SendTextRequest,
    settings: Settings = Depends(get_settings),
) -> ApiResponse:
    try:
        result = run_wacli(
            ["send", "text", "--to", req.to, "--body", req.body],
            timeout=settings.timeout,
        )
        return ApiResponse(success=True, data=result.get("data"))
    except RuntimeError as exc:
        return ApiResponse(success=False, error=str(exc))


@router.post("/send/file")
def send_file(
    to: str,
    file: UploadFile,
    settings: Settings = Depends(get_settings),
) -> ApiResponse:
    suffix = Path(file.filename or "upload").suffix
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(file.file.read())
            tmp_path = tmp.name
        result = run_wacli(
            ["send", "file", "--to", to, "--file", tmp_path],
            timeout=settings.timeout,
        )
        return ApiResponse(success=True, data=result.get("data"))
    except RuntimeError as exc:
        return ApiResponse(success=False, error=str(exc))
    finally:
        Path(tmp_path).unlink(missing_ok=True)
