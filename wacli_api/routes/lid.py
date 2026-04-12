"""LID resolution endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from wacli_api import lid
from wacli_api.deps import get_settings, verify_api_key
from wacli_api.schemas import ApiResponse
from wacli_api.settings import Settings

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.get("/lid/resolve")
def resolve_lid(jid: str) -> ApiResponse[dict[str, str]]:
    resolved = lid.normalize_jid(jid)
    return ApiResponse(success=True, data={"original": jid, "resolved": resolved})


@router.get("/lid/map")
def get_lid_map() -> ApiResponse[dict[str, str]]:
    return ApiResponse(success=True, data=lid.get_map())


@router.post("/lid/reload")
def reload_lid_map(
    settings: Settings = Depends(get_settings),
) -> ApiResponse[dict[str, int]]:
    lid.reload(settings.session_db)
    return ApiResponse(success=True, data={"count": len(lid.get_map())})
