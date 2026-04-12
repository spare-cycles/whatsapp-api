"""MCP server exposing the whatsapp-api as tools (Streamable HTTP transport)."""

from __future__ import annotations

import os

import httpx
from fastmcp import FastMCP

_BASE = os.environ.get("WACLI_API_BASE_URL", "http://whatsapp-api:9471")
_KEY = os.environ.get("WACLI_API_KEY", "")

mcp = FastMCP("whatsapp")
_client = httpx.Client(
    base_url=_BASE,
    headers={"X-API-Key": _KEY} if _KEY else {},
    timeout=30,
)


@mcp.tool()
def list_chats(limit: int = 50) -> object:
    """List recent WhatsApp conversations ordered by last message."""
    return _client.get("/chats", params={"limit": limit}).json()


@mcp.tool()
def get_messages(
    chat: str,
    after: str = "",
    before: str = "",
    limit: int = 100,
) -> object:
    """Fetch messages from a chat. after/before: YYYY-MM-DD or RFC3339. Newest first."""
    params: dict[str, str | int] = {"chat": chat, "limit": limit}
    if after:
        params["after"] = after
    if before:
        params["before"] = before
    return _client.get("/messages", params=params).json()


@mcp.tool()
def search_messages(query: str) -> object:
    """Full-text search across all WhatsApp messages (FTS5). Returns newest first."""
    return _client.get("/messages/search", params={"query": query}).json()


@mcp.tool()
def get_contact(jid: str) -> object:
    """Resolve a JID to contact info (name, phone, alias, tags)."""
    return _client.get("/contacts", params={"jid": jid}).json()


@mcp.tool()
def search_contacts(query: str) -> object:
    """Search contacts by name, phone, or alias."""
    return _client.get("/contacts/search", params={"query": query}).json()


@mcp.tool()
def list_groups(limit: int = 50) -> object:
    """List WhatsApp groups with owner and timestamps."""
    return _client.get("/groups", params={"limit": limit}).json()


@mcp.tool()
def send_message(to: str, body: str) -> object:
    """Send a WhatsApp text message. `to` is a JID (e.g. 33650633719@s.whatsapp.net)."""
    return _client.post("/send/text", json={"to": to, "body": body}).json()


@mcp.tool()
def resolve_lid(jid: str) -> object:
    """Resolve a legacy @lid JID to its phone-based @s.whatsapp.net equivalent."""
    return _client.get("/lid/resolve", params={"jid": jid}).json()


if __name__ == "__main__":
    # path="/" because Tailscale strips the /mcp mount prefix before forwarding
    # (confirmed: ipnlocal/serve.go uses http.StripPrefix, issue #6571)
    mcp.run(transport="streamable-http", host="0.0.0.0", port=9472, path="/")
