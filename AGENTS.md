# AGENTS.md — whatsapp-api

Instructions for AI coding agents (Claude Code, Codex, Copilot, etc.) working in this repository.

## Tech Stack

- **Language:** Python 3.13 (strict typing enforced via Pyright)
- **Framework:** FastAPI with Pydantic v2
- **Queue:** Redis 7 (send jobs only; all reads are direct SQLite)
- **Databases:** SQLite (read-only in the API; `wacli.db` for messages/chats/contacts, `session.db` for LID mapping)
- **Package manager:** Poetry
- **Linter/formatter:** Ruff
- **Type checker:** Pyright (strict mode)
- **Test framework:** pytest + httpx

## Commands

```bash
# Install dependencies
poetry install

# Run the dev API server (requires a Redis instance at redis://localhost:6379)
poetry run uvicorn wacli_api.main:app --reload --port 9471

# Run tests
poetry run pytest

# Run a single test file
poetry run pytest tests/test_routes_health.py -v

# Lint
poetry run ruff check .

# Format check
poetry run ruff format --check .

# Auto-fix lint + format
poetry run ruff check --fix . && poetry run ruff format .

# Type check
poetry run pyright

# Docker: build and start all services
docker compose up -d --build

# Docker: view logs
docker compose logs -f whatsapp-api
docker compose logs -f wacli-sync
```

## Architecture

The project has two distinct runtime targets built from the same Dockerfile:

- **`whatsapp-api` (api target):** FastAPI service. Handles all HTTP requests. For read operations (chats, messages, contacts), it queries SQLite directly (read-only). For write operations (send text/file), it pushes a job to the Redis queue `wacli:send` and blocks waiting for a reply on `wacli:send:reply:{job_id}`.

- **`wacli-sync` (sync target):** Two processes in one container. `wacli sync --follow --refresh-groups` keeps the SQLite databases up to date by syncing from WhatsApp. `sync_worker.py` consumes the Redis send queue and calls the `wacli` binary via subprocess.

The API container mounts `wacli-data` **read-only**. Only `wacli-sync` has write access to the SQLite files.

```
HTTP request (read)  → FastAPI → SQLite (wacli.db / session.db) → response
HTTP request (write) → FastAPI → Redis queue → sync_worker.py → wacli subprocess → Redis reply → response
```

## Project Structure

```
wacli_api/
  main.py         # App factory, lifespan (Redis connect, LID reload), router registration
  settings.py     # All config via WACLI_-prefixed env vars
  deps.py         # FastAPI dependencies: get_settings(), get_redis(), verify_api_key()
  db.py           # get_db() read-only SQLite context manager; time parsing helpers
  lid.py          # In-memory LID→phone JID map, loaded at startup from session.db
  schemas.py      # ApiResponse, SendTextRequest — keep this minimal
  routes/         # One file per resource group
sync_worker.py    # Standalone Redis consumer (not imported by wacli_api)
```

## Code Conventions

**Response shape:** Every endpoint returns `ApiResponse(success=bool, data=..., error=...)`. Never return a bare dict or raise HTTP exceptions for business-logic failures — set `success=False` and return a 200.

**Dependencies:** Use `Depends()` for `get_settings()`, `get_redis()`, and `verify_api_key()`. Do not instantiate `Settings()` or Redis clients inside route handlers.

**Database access:** Always use `get_db(settings.store_db)` as a context manager. Never hold a connection open across await points. Queries must be read-only (no INSERT/UPDATE/DELETE in `wacli_api/`).

**Type annotations:** All functions must be fully annotated. Pyright runs in strict mode — no `Any` without a `# type: ignore[...]` comment explaining why.

**Imports:** Use `from __future__ import annotations` at the top of every module. Group imports: stdlib → third-party → local, separated by blank lines (Ruff/isort enforces this).

**No subprocess in routes:** The API never calls `wacli` directly. Subprocess calls live exclusively in `sync_worker.py`.

## Testing

Tests live in `tests/`. Fixtures are in `conftest.py` — use `client` (no auth) and `authed_client` (with `X-API-Key`).

- Mock at the boundary closest to the test subject (e.g. patch `get_db`, not the entire SQLite module).
- Do not use real SQLite files in tests — use `:memory:` or monkeypatching.
- Keep tests focused: one behavior per test function.

## Boundaries

**Always do:**
- Run `ruff check .` and `pyright` before considering a change complete.
- Keep `sync_worker.py` and `wacli_api/` decoupled — they share only the Redis queue protocol (JSON job format).

**Ask first:**
- Before adding a new Python dependency (`poetry add …`).
- Before changing the Redis queue schema (`wacli:send` job format or reply format) — `sync_worker.py` and `send.py` must stay in sync.
- Before modifying `docker-compose.yaml` service definitions.

**Never do:**
- Commit secrets or API keys.
- Add INSERT/UPDATE/DELETE SQL to any file under `wacli_api/` — the API is strictly read-only on the databases.
- Skip `--no-verify` or bypass pre-commit hooks.
- Add direct `wacli` subprocess calls inside `wacli_api/` routes.
