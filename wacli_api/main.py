"""FastAPI application entry point."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from wacli_api import lid
from wacli_api.routes import chats, contacts, groups, health, lid as lid_routes, messages, send
from wacli_api.settings import Settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    app.state.settings = settings
    lid.reload(settings.session_db)
    yield


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
