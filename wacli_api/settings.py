"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="WACLI_")

    api_key: str | None = None
    api_host: str = "0.0.0.0"
    api_port: int = 9471
    session_db: str = "/root/.wacli/session.db"
    timeout: int = 60  # subprocess timeout in seconds
    log_level: str = "INFO"
