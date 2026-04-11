"""Health check endpoint — no authentication required."""

from __future__ import annotations

import redis as _redis
from fastapi import APIRouter, Depends

from wacli_api.db import get_db
from wacli_api.deps import get_redis, get_settings
from wacli_api.schemas import ApiResponse
from wacli_api.settings import Settings

router = APIRouter()


@router.get("/health")
def health(
    settings: Settings = Depends(get_settings),
    r: _redis.Redis = Depends(get_redis),  # type: ignore[type-arg]
) -> ApiResponse:
    try:
        with get_db(settings.store_db) as conn:
            conn.execute("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False

    try:
        r.ping()
        redis_ok = True
    except Exception:
        redis_ok = False

    # Only SQLite failure makes the endpoint unhealthy (→ Docker healthcheck restart).
    # Redis failure is reported but does not trigger a container restart.
    return ApiResponse(success=db_ok, data={"db": db_ok, "redis": redis_ok})
