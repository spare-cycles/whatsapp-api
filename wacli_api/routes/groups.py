"""Group endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from wacli_api.deps import get_settings, verify_api_key
from wacli_api.schemas import ApiResponse
from wacli_api.settings import Settings
from wacli_api.wacli import extract_data_list, run_wacli

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.get("/groups")
def list_groups(
    limit: int = 10000,
    settings: Settings = Depends(get_settings),
) -> ApiResponse:
    try:
        result = run_wacli(
            ["groups", "list", "--limit", str(limit)], timeout=settings.timeout
        )
        return ApiResponse(success=True, data=extract_data_list(result))
    except RuntimeError as exc:
        return ApiResponse(success=False, error=str(exc))


@router.get("/groups/show")
def show_group(
    jid: str,
    settings: Settings = Depends(get_settings),
) -> ApiResponse:
    try:
        result = run_wacli(
            ["groups", "info", "--jid", jid], timeout=settings.timeout
        )
        return ApiResponse(success=True, data=result.get("data"))
    except RuntimeError as exc:
        return ApiResponse(success=False, error=str(exc))
