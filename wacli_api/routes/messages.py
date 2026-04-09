"""Message endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from wacli_api.deps import get_settings, verify_api_key
from wacli_api.schemas import ApiResponse
from wacli_api.settings import Settings
from wacli_api.wacli import extract_data_list, extract_nested_list, run_wacli

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.get("/messages")
def list_messages(
    chat: str,
    after: str | None = None,
    before: str | None = None,
    limit: int = 10000,
    settings: Settings = Depends(get_settings),
) -> ApiResponse:
    args = ["messages", "list", "--chat", chat, "--limit", str(limit)]
    if after:
        args.extend(["--after", after])
    if before:
        args.extend(["--before", before])
    try:
        result = run_wacli(args, timeout=settings.timeout)
        messages = extract_nested_list(result, "data", "messages")
        return ApiResponse(success=True, data={"messages": messages})
    except RuntimeError as exc:
        return ApiResponse(success=False, error=str(exc))


@router.get("/messages/search")
def search_messages(
    query: str,
    settings: Settings = Depends(get_settings),
) -> ApiResponse:
    try:
        result = run_wacli(
            ["messages", "search", "--query", query], timeout=settings.timeout
        )
        return ApiResponse(success=True, data=extract_data_list(result))
    except RuntimeError as exc:
        return ApiResponse(success=False, error=str(exc))
