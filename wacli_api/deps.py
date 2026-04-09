"""FastAPI dependencies: settings and API key auth."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request
from fastapi.security import APIKeyHeader

from wacli_api.settings import Settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_settings(request: Request) -> Settings:
    """Return the Settings instance stored on app.state."""
    return request.app.state.settings  # type: ignore[no-any-return]


def verify_api_key(
    settings: Settings = Depends(get_settings),
    api_key: str | None = Depends(_api_key_header),
) -> None:
    """Check X-API-Key header. Skip if api_key is not configured (dev mode)."""
    if settings.api_key is None:
        return
    if api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
