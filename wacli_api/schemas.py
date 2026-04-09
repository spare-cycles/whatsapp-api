"""Pydantic request/response models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    success: bool
    data: Any = None
    error: str | None = None


class SendTextRequest(BaseModel):
    to: str
    body: str
