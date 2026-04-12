# WhatsApp API Documentation

Internal HTTP API wrapping the [wacli](https://github.com/steipete/wacli) WhatsApp CLI. Provides WhatsApp messaging capabilities to other containers on the `wacli-net` Docker network.

**Base URL:** `http://whatsapp-api:9471` (internal only, no host port exposed)

## Authentication

All endpoints except `/health` require an `X-API-Key` header.

```
X-API-Key: <your-api-key>
```

If `WACLI_API_KEY` is not set in `.env`, authentication is disabled (dev mode).

## Response Format

Every endpoint returns the same JSON envelope:

```json
{
  "success": true,
  "data": <endpoint-specific>,
  "error": null
}
```

On failure:

```json
{
  "success": false,
  "data": null,
  "error": "description of what went wrong"
}
```

## JID Format

WhatsApp identifies users and groups with JIDs (Jabber IDs):

| Type | Format | Example |
|------|--------|---------|
| Personal | `<phone>@s.whatsapp.net` | `33650633719@s.whatsapp.net` |
| Group | `<id>@g.us` | `120363044123456789@g.us` |
| LID (legacy) | `<lid>@lid` | `195769072144617@lid` |

JIDs are always passed as **query parameters**, never in the URL path, to avoid encoding issues with `@`.

## Configuration

Environment variables (all prefixed with `WACLI_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `WACLI_API_KEY` | _(none)_ | API key for authentication. Unset = no auth. |
| `WACLI_API_HOST` | `0.0.0.0` | Bind address |
| `WACLI_API_PORT` | `9471` | Listen port |
| `WACLI_SESSION_DB` | `/root/.wacli/session.db` | Path to wacli's SQLite session database (LID mapping) |
| `WACLI_STORE_DB` | `/root/.wacli/wacli.db` | Path to wacli's main SQLite database (messages, chats, contacts) |
| `WACLI_REDIS_URL` | `redis://redis:6379` | Redis connection URL |
| `WACLI_TIMEOUT` | `60` | Send job timeout in seconds |
| `WACLI_LOG_LEVEL` | `INFO` | Logging level |

---

## Endpoints

### Health

#### `GET /health`

Check infrastructure status (SQLite + Redis reachability). **No API key required.** Used as the Docker healthcheck.

`success` is `false` if SQLite is unreachable (triggers container restart). Redis failure is reported but does not affect `success`.

**Request:**

```
GET /health
```

**Response:**

```json
{
  "success": true,
  "data": {
    "db": true,
    "redis": true
  }
}
```

If SQLite is down:

```json
{
  "success": false,
  "data": {
    "db": false,
    "redis": true
  }
}
```

---

### Chats

#### `GET /chats`

List all WhatsApp conversations, ordered by most recent message.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 10000 | Maximum number of chats to return |

**Request:**

```
GET /chats?limit=5
```

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "JID": "33650633719@s.whatsapp.net",
      "Kind": "personal",
      "Name": "Alice",
      "LastMessageTS": "2026-04-08T14:30:00Z"
    }
  ]
}
```

#### `GET /chats/show`

Get details for a single chat.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `jid` | string | yes | Chat JID |

**Request:**

```
GET /chats/show?jid=33650633719@s.whatsapp.net
```

**Response:**

```json
{
  "success": true,
  "data": {
    "JID": "33650633719@s.whatsapp.net",
    "Kind": "personal",
    "Name": "Alice",
    "LastMessageTS": "2026-04-08T14:30:00Z"
  }
}
```

If not found: `success: false`, `error: "chat not found"`.

---

### Groups

#### `GET /groups`

List all WhatsApp groups.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 10000 | Maximum number of groups to return |

**Request:**

```
GET /groups?limit=100
```

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "JID": "120363044123456789@g.us",
      "Name": "Family Chat",
      "OwnerJID": "33650633719@s.whatsapp.net",
      "CreatedAt": "2024-01-15T10:00:00Z",
      "UpdatedAt": "2026-04-08T14:30:00Z"
    }
  ]
}
```

#### `GET /groups/show`

Get group info from the local cache, including participants.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `jid` | string | yes | Group JID |

**Request:**

```
GET /groups/show?jid=120363044123456789@g.us
```

**Response:**

```json
{
  "success": true,
  "data": {
    "JID": "120363044123456789@g.us",
    "Name": "Family Chat",
    "OwnerJID": "33650633719@s.whatsapp.net",
    "CreatedAt": "2024-01-15T10:00:00Z",
    "UpdatedAt": "2026-04-08T14:30:00Z",
    "Participants": [
      {"UserJID": "33650633719@s.whatsapp.net", "Role": "admin"},
      {"UserJID": "14155551234@s.whatsapp.net", "Role": "member"}
    ]
  }
}
```

If not found: `success: false`, `error: "group not found"`.

---

### Messages

#### `GET /messages`

Fetch messages from a specific chat within a time range, ordered by most recent first.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `chat` | string | yes | | Chat JID |
| `after` | string | no | | Start timestamp (RFC3339 or YYYY-MM-DD). Exclusive. |
| `before` | string | no | | End timestamp (RFC3339 or YYYY-MM-DD). Exclusive. |
| `limit` | int | no | 10000 | Maximum messages to return |

**Request:**

```
GET /messages?chat=33650633719@s.whatsapp.net&after=2026-04-01&before=2026-04-09&limit=100
```

**Response:**

```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "ChatJID":     "33650633719@s.whatsapp.net",
        "ChatName":    "Alice",
        "MsgID":       "3EB0A1B2C3D4E5F6",
        "SenderJID":   "33650633719@s.whatsapp.net",
        "Timestamp":   "2026-04-05T10:30:00Z",
        "FromMe":      false,
        "Text":        "Hello!",
        "DisplayText": "",
        "MediaType":   "",
        "Snippet":     ""
      }
    ]
  }
}
```

`DisplayText` holds caption text for media messages. `MediaType` is non-empty for media messages (e.g. `"image"`, `"video"`, `"audio"`, `"document"`). `Snippet` is only populated by the search endpoint (always `""` here).

If the time format is invalid: `success: false`, `error: "invalid time format (use RFC3339 or YYYY-MM-DD)"`.

#### `GET /messages/search`

Full-text search across all messages using SQLite FTS5. Returns results ordered by most recent first.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | yes | FTS5 search query |

**Request:**

```
GET /messages/search?query=meeting+tomorrow
```

**Response:**

```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "ChatJID":     "33650633719@s.whatsapp.net",
        "ChatName":    "Alice",
        "MsgID":       "3EB0A1B2C3D4E5F6",
        "SenderJID":   "33650633719@s.whatsapp.net",
        "Timestamp":   "2026-04-07T16:00:00Z",
        "FromMe":      false,
        "Text":        "Let's have a meeting tomorrow at 3pm",
        "DisplayText": "",
        "MediaType":   "",
        "Snippet":     "Let's have a meeting tomorrow…"
      }
    ]
  }
}
```

`Snippet` contains an FTS5-extracted excerpt (up to 20 tokens) with the match context.

---

### Contacts

#### `GET /contacts`

Resolve a WhatsApp JID to contact information. If the JID is not found in the local database, a minimal response is returned using the phone number derived from the JID.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `jid` | string | yes | Contact JID |

**Request:**

```
GET /contacts?jid=33650633719@s.whatsapp.net
```

**Response (contact found):**

```json
{
  "success": true,
  "data": {
    "JID":          "33650633719@s.whatsapp.net",
    "Phone":        "+33650633719",
    "Alias":        "",
    "Name":         "Alice Dupont",
    "Tags":         ["family"],
    "UpdatedAt":    "2026-03-01T09:00:00Z",
    "display_name": "Alice Dupont"
  }
}
```

**Response (contact not found in DB):**

```json
{
  "success": true,
  "data": {
    "JID":          "33650633719@s.whatsapp.net",
    "display_name": "+33650633719"
  }
}
```

`Name` is resolved in priority order: `full_name` → `push_name` → `business_name` → `first_name`. `display_name` falls back to the phone number extracted from the JID if `Name` is empty. `Alias` is sourced from the `contact_aliases` table.

#### `GET /contacts/search`

Search contacts by name, phone, or alias.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | yes | Substring to match against name fields, phone, and alias |

**Request:**

```
GET /contacts/search?query=alice
```

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "JID":          "33650633719@s.whatsapp.net",
      "Phone":        "+33650633719",
      "Alias":        "",
      "Name":         "Alice Dupont",
      "Tags":         ["family"],
      "UpdatedAt":    "2026-03-01T09:00:00Z",
      "display_name": "Alice Dupont"
    }
  ]
}
```

Matches against `full_name`, `push_name`, `first_name`, `business_name`, `phone`, and `alias` (case-insensitive substring search).

---

### Send

#### `POST /send/text`

Send a text message. Blocks until the `wacli-sync` worker confirms delivery or the timeout elapses.

**Request body (JSON):**

```json
{
  "to": "33650633719@s.whatsapp.net",
  "body": "Hello from the API!"
}
```

**curl example:**

```bash
curl -X POST http://whatsapp-api:9471/send/text \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"to": "33650633719@s.whatsapp.net", "body": "Hello!"}'
```

**Response:**

```json
{
  "success": true,
  "data": {
    "MessageID": "3EB0A1B2C3D4E5F6",
    "Timestamp": "2026-04-09T12:00:00Z"
  }
}
```

On timeout: `success: false`, `error: "send timed out"`.

#### `POST /send/file`

Send a file (image, video, audio, document). Uses multipart form upload. Blocks until confirmed or timeout.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `to` | string | yes | Recipient JID |
| `file` | file | yes | File to send |

**curl example:**

```bash
curl -X POST http://whatsapp-api:9471/send/file \
  -H "X-API-Key: your-key" \
  -F "to=33650633719@s.whatsapp.net" \
  -F "file=@photo.jpg"
```

**Response:**

```json
{
  "success": true,
  "data": {
    "MessageID": "3EB0A1B2C3D4E5F6",
    "Timestamp": "2026-04-09T12:00:00Z"
  }
}
```

On timeout: `success: false`, `error: "send timed out"`.

---

### LID Resolution

WhatsApp's legacy LID format (`@lid`) can be converted to standard phone-based JIDs (`@s.whatsapp.net`) using mappings from wacli's session database.

#### `GET /lid/resolve`

Resolve a single LID JID to its phone-based equivalent.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `jid` | string | yes | JID to resolve |

**Request:**

```
GET /lid/resolve?jid=195769072144617@lid
```

**Response:**

```json
{
  "success": true,
  "data": {
    "original": "195769072144617@lid",
    "resolved": "33650633719@s.whatsapp.net"
  }
}
```

If the JID is not an `@lid` or no mapping exists, `resolved` returns the original JID unchanged.

#### `GET /lid/map`

Return the full LID-to-phone mapping table. Useful for bulk resolution by consumers that need to resolve many JIDs at once (e.g. during message ingestion).

**Request:**

```
GET /lid/map
```

**Response:**

```json
{
  "success": true,
  "data": {
    "195769072144617": "33650633719",
    "233663467929724": "14155551234"
  }
}
```

Keys are bare LID numbers, values are phone numbers (without `@s.whatsapp.net` suffix).

#### `POST /lid/reload`

Reload the LID mapping table from wacli's session database. Call this after a fresh `wacli sync` to pick up new mappings.

**Request:**

```
POST /lid/reload
```

**Response:**

```json
{
  "success": true,
  "data": {
    "count": 42
  }
}
```

---

## Error Handling

All errors return HTTP 200 with `"success": false` in the body (not HTTP error codes), except:

| HTTP Status | Cause |
|-------------|-------|
| 401 | Missing or invalid `X-API-Key` |
| 422 | Malformed request (missing required params, bad JSON) |

Application errors (wacli failures, timeouts) are returned in the envelope:

```json
{
  "success": false,
  "data": null,
  "error": "send timed out"
}
```

## Docker Network

This service runs on the `wacli-net` external Docker network with no host port exposed. Consumers must join `wacli-net` in their own `docker-compose.yaml`:

```yaml
services:
  my-service:
    networks:
      - wacli-net

networks:
  wacli-net:
    external: true
```

Then access the API at `http://whatsapp-api:9471`.

## Initial Setup

After first deployment, authenticate with WhatsApp:

```bash
docker exec -it whatsapp-api wacli auth
```

Scan the QR code with WhatsApp on your phone. The session persists in the `wacli-data` Docker volume.
