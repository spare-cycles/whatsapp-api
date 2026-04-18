"""FastAPI application entry point."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import urlparse

import redis as _redis
import uvicorn
from fastapi import FastAPI

from wacli_api import lid
from wacli_api.database import make_engine
from wacli_api.routes import chats, contacts, groups, health, messages, send
from wacli_api.routes import lid as lid_routes
from wacli_api.settings import Settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(level=log_level)
    app.state.settings = settings
    app.state.engine = make_engine(settings.store_db)
    parsed = urlparse(settings.redis_url)
    redis_raw: Any = _redis.Redis(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        db=int((parsed.path or "").lstrip("/") or "0"),
        password=parsed.password,
        username=parsed.username or None,
        decode_responses=True,
    )
    app.state.redis = redis_raw
    lid.reload(settings.session_db)
    yield
    app.state.redis.close()
    app.state.engine.dispose()


app = FastAPI(title="wacli API", lifespan=lifespan)

app.include_router(health.router)
app.include_router(chats.router)
app.include_router(groups.router)
app.include_router(messages.router)
app.include_router(contacts.router)
app.include_router(send.router)
app.include_router(lid_routes.router)


def run() -> None:
    settings = Settings()
    uvicorn.run(
        "wacli_api.main:app",
        host=settings.api_host,
        port=settings.api_port,
    )
