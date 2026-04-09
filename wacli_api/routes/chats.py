"""Chat endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from wacli_api.deps import get_settings, verify_api_key
from wacli_api.schemas import ApiResponse
from wacli_api.settings import Settings
from wacli_api.wacli import extract_data_list, run_wacli

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.get("/chats")
def list_chats(
    limit: int = 10000,
    settings: Settings = Depends(get_settings),
) -> ApiResponse:
    try:
        result = run_wacli(
            ["chats", "list", "--limit", str(limit)], timeout=settings.timeout
        )
        return ApiResponse(success=True, data=extract_data_list(result))
    except RuntimeError as exc:
        return ApiResponse(success=False, error=str(exc))


@router.get("/chats/show")
def show_chat(
    jid: str,
    settings: Settings = Depends(get_settings),
) -> ApiResponse:
    try:
        result = run_wacli(
            ["chats", "show", "--jid", jid], timeout=settings.timeout
        )
        return ApiResponse(success=True, data=result.get("data"))
    except RuntimeError as exc:
        return ApiResponse(success=False, error=str(exc))
