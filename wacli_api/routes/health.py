"""Health check endpoint — no authentication required."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text as sa_text
from sqlalchemy.engine import Engine

from wacli_api.database import get_engine
from wacli_api.deps import get_redis
from wacli_api.redis_types import RedisClient
from wacli_api.schemas import ApiResponse

router = APIRouter()


@router.get("/health")
def health(
    engine: Engine = Depends(get_engine),
    r: RedisClient = Depends(get_redis),
) -> ApiResponse[dict[str, bool]]:
    try:
        with engine.connect() as conn:
            conn.execute(sa_text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    try:
        r.ping()
        redis_ok = True
    except Exception:
        redis_ok = False

    return ApiResponse(
        success=db_ok and redis_ok, data={"db": db_ok, "redis": redis_ok}
    )
