"""Health check endpoint — no authentication required."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from wacli_api.deps import get_settings
from wacli_api.schemas import ApiResponse
from wacli_api.settings import Settings
from wacli_api.wacli import run_wacli

router = APIRouter()


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> ApiResponse:
    try:
        result = run_wacli(["auth", "status"], timeout=settings.timeout)
        return ApiResponse(success=True, data=result.get("data"))
    except RuntimeError as exc:
        return ApiResponse(success=False, error=str(exc))
