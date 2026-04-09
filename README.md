# whatsapp-api

Internal HTTP API for WhatsApp, wrapping the [wacli](https://github.com/steipete/wacli) CLI.

## Overview

whatsapp-api is a lightweight FastAPI service that provides WhatsApp messaging capabilities over HTTP. It exists so that multiple Docker containers can share a single WhatsApp session without SQLite locking conflicts or duplicate wacli installations. One container owns the session; everyone else talks HTTP.

Built for the internal `wacli-net` Docker network. No host port exposed.

## Architecture

```
+------------------+     +------------------+
|  tasks-monitor   |     |   loup-openclaw  |
|                  |     |                  |
+--------+---------+     +--------+---------+
         |                        |
         |   HTTP (wacli-net)     |
         +----------+-------------+
                    |
           +--------v---------+
           |   whatsapp-api   |
           |   :9471          |
           +--------+---------+
                    |
              subprocess
                    |
           +--------v---------+
           |      wacli       |
           |  (Go binary)     |
           +--------+---------+
                    |
           WhatsApp servers
```

## Prerequisites

- Docker and Docker Compose
- A phone with WhatsApp (for QR code pairing)

## Quick Start

```bash
# 1. Create the shared network (once)
docker network create wacli-net

# 2. Configure
cp .env.example .env   # or set WACLI_API_KEY in .env

# 3. Build and start
docker compose up -d --build

# 4. Pair with WhatsApp
docker exec -it whatsapp-api wacli auth
# Scan the QR code with your phone
```

Verify it's running:

```bash
docker exec whatsapp-api curl -fsS http://127.0.0.1:9471/health
# {"success":true,"data":{"authenticated":true,...}}
```

## Configuration

All environment variables are prefixed with `WACLI_` and loaded from `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `WACLI_API_KEY` | _(none)_ | Shared secret for `X-API-Key` header. Unset = no auth (dev mode). |
| `WACLI_API_HOST` | `0.0.0.0` | Bind address |
| `WACLI_API_PORT` | `9471` | Listen port |
| `WACLI_SESSION_DB` | `/root/.wacli/session.db` | Path to wacli's SQLite session database |
| `WACLI_TIMEOUT` | `60` | Subprocess timeout in seconds |
| `WACLI_LOG_LEVEL` | `INFO` | Python logging level |

## API Reference

All endpoints return `{"success": bool, "data": ..., "error": ...}`. Authentication via `X-API-Key` header (except `/health`).

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Auth status check (no API key required) |
| GET | `/chats` | List conversations |
| GET | `/chats/show?jid=` | Single chat details |
| GET | `/groups` | List groups |
| GET | `/groups/show?jid=` | Group info (live) |
| GET | `/messages?chat=&after=&before=` | Fetch messages by date range |
| GET | `/messages/search?query=` | Full-text search |
| GET | `/contacts?jid=` | Resolve contact name |
| GET | `/contacts/search?query=` | Search contacts |
| POST | `/send/text` | Send a text message |
| POST | `/send/file` | Send a file (multipart) |
| GET | `/lid/resolve?jid=` | Resolve legacy LID JID |
| GET | `/lid/map` | Full LID-to-phone mapping |
| POST | `/lid/reload` | Reload LID map from session DB |

See [APIDOCS.md](APIDOCS.md) for full request/response details, parameters, and curl examples.

## Consumer Integration

Other containers connect by joining the `wacli-net` network:

```yaml
# In your docker-compose.yaml
services:
  my-app:
    # ...
    environment:
      - WACLI_API_URL=http://whatsapp-api:9471
      - WACLI_API_KEY=${WACLI_API_KEY}
    networks:
      - wacli-net

networks:
  wacli-net:
    external: true
```

Then call the API from your code:

```python
import httpx

client = httpx.Client(
    base_url="http://whatsapp-api:9471",
    headers={"X-API-Key": api_key},
)
resp = client.get("/chats", params={"limit": 100})
chats = resp.json()["data"]
```

## Development

Run the dev server locally (requires Python 3.13+ and wacli installed):

```bash
poetry install
poetry run uvicorn wacli_api.main:app --reload --port 9471
```

Run tests:

```bash
poetry run pytest
```

Lint and type check:

```bash
poetry run ruff check .
poetry run ruff format --check .
poetry run pyright
```

## Project Structure

```
whatsapp-api/
  Dockerfile              # Multi-stage: Go wacli build + Python runtime
  docker-compose.yaml     # Service definition (wacli-net, wacli-data volume)
  pyproject.toml          # Poetry project config
  APIDOCS.md              # Full API documentation
  .env                    # WACLI_API_KEY and other config
  wacli_api/
    main.py               # FastAPI app, lifespan, router setup
    settings.py           # pydantic-settings configuration
    deps.py               # API key auth dependency
    wacli.py              # Subprocess wrapper for wacli CLI
    lid.py                # LID-to-phone JID resolution (reads session.db)
    schemas.py            # Pydantic request/response models
    routes/
      health.py           # GET /health (unauthenticated)
      chats.py            # Chat list and details
      groups.py           # Group list and info
      messages.py         # Message list and search
      contacts.py         # Contact lookup and search
      send.py             # Send text and files
      lid.py              # LID resolution and map
  tests/
    conftest.py           # Test fixtures (client, authed_client)
    test_wacli.py         # Subprocess wrapper tests
    test_lid.py           # LID normalization tests
    test_routes_health.py # Health endpoint + auth tests
```
