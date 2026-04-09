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
| `WACLI_SESSION_DB` | `/root/.wacli/session.db` | Path to wacli's SQLite session database |
| `WACLI_TIMEOUT` | `60` | Subprocess timeout in seconds |
| `WACLI_LOG_LEVEL` | `INFO` | Logging level |

---

## Endpoints

### Health

#### `GET /health`

Check WhatsApp authentication status. **No API key required.** Used as the Docker healthcheck.

**Request:**

```
GET /health
```

**Response:**

```json
{
  "success": true,
  "data": {
    "authenticated": true,
    "phone": "33650633719",
    "platform": "smba",
    "pushName": "Loup"
  }
}
```

If not authenticated:

```json
{
  "success": true,
  "data": {
    "authenticated": false
  }
}
```

---

### Chats

#### `GET /chats`

List all WhatsApp conversations.

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
      "Name": "Alice",
      "LastMessageTimestamp": "2026-04-08T14:30:00Z",
      "UnreadCount": 0
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
    "Name": "Alice",
    "LastMessageTimestamp": "2026-04-08T14:30:00Z"
  }
}
```

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
      "ParticipantCount": 5
    }
  ]
}
```

#### `GET /groups/show`

Get live group info (fetched from WhatsApp servers, not local cache).

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
    "Topic": "Weekend plans",
    "Participants": [
      {"JID": "33650633719@s.whatsapp.net", "IsAdmin": true}
    ]
  }
}
```

---

### Messages

#### `GET /messages`

Fetch messages from a specific chat within a time range.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `chat` | string | yes | | Chat JID |
| `after` | string | no | | Start date (YYYY-MM-DD) |
| `before` | string | no | | End date (YYYY-MM-DD) |
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
        "MsgID": "3EB0A1B2C3D4E5F6",
        "Timestamp": "2026-04-05T10:30:00Z",
        "FromMe": false,
        "SenderJID": "33650633719@s.whatsapp.net",
        "Text": "Hello!",
        "Body": "Hello!"
      }
    ]
  }
}
```

#### `GET /messages/search`

Full-text search across all messages (uses SQLite FTS5 when available).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | yes | Search query |

**Request:**

```
GET /messages/search?query=meeting+tomorrow
```

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "MsgID": "3EB0A1B2C3D4E5F6",
      "ChatJID": "33650633719@s.whatsapp.net",
      "Text": "Let's have a meeting tomorrow at 3pm",
      "Timestamp": "2026-04-07T16:00:00Z"
    }
  ]
}
```

---

### Contacts

#### `GET /contacts`

Resolve a WhatsApp JID to contact information.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `jid` | string | yes | Contact JID |

**Request:**

```
GET /contacts?jid=33650633719@s.whatsapp.net
```

**Response:**

```json
{
  "success": true,
  "data": {
    "JID": "33650633719@s.whatsapp.net",
    "Name": "Alice Dupont",
    "FullName": "Alice Dupont",
    "PushName": "Alice"
  }
}
```

#### `GET /contacts/search`

Search contacts by name.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | yes | Search query |

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
      "JID": "33650633719@s.whatsapp.net",
      "Name": "Alice Dupont",
      "PushName": "Alice"
    }
  ]
}
```

---

### Send

#### `POST /send/text`

Send a text message.

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

#### `POST /send/file`

Send a file (image, video, audio, document). Uses multipart form upload.

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
  "error": "wacli failed (exit 1): session not found"
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
