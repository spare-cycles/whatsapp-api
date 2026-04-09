"""Contact endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from wacli_api.deps import get_settings, verify_api_key
from wacli_api.schemas import ApiResponse
from wacli_api.settings import Settings
from wacli_api.wacli import extract_data_list, run_wacli

router = APIRouter(dependencies=[Depends(verify_api_key)])


def _phone_from_jid(jid: str) -> str:
    """Extract a phone number from a JID.

    Example: '33782300839@s.whatsapp.net' -> '+33782300839'.
    Returns the original JID if no phone number can be extracted.
    """
    local = jid.split("@")[0].split(":")[0]
    if local.isdigit():
        return f"+{local}"
    return jid


@router.get("/contacts")
def show_contact(
    jid: str,
    settings: Settings = Depends(get_settings),
) -> ApiResponse:
    try:
        result = run_wacli(
            ["contacts", "show", "--jid", jid], timeout=settings.timeout
        )
        data = result.get("data")
        if isinstance(data, dict):
            # Inject a display_name field with phone fallback
            name = (
                data.get("Name")
                or data.get("FullName")
                or data.get("PushName")
                or data.get("name")
            )
            data["display_name"] = name if name else _phone_from_jid(jid)
        return ApiResponse(success=True, data=data)
    except RuntimeError:
        # Contact not found — return phone number fallback instead of error
        return ApiResponse(
            success=True,
            data={"JID": jid, "display_name": _phone_from_jid(jid)},
        )


@router.get("/contacts/search")
def search_contacts(
    query: str,
    settings: Settings = Depends(get_settings),
) -> ApiResponse:
    try:
        result = run_wacli(
            ["contacts", "search", "--query", query], timeout=settings.timeout
        )
        return ApiResponse(success=True, data=extract_data_list(result))
    except RuntimeError as exc:
        return ApiResponse(success=False, error=str(exc))
