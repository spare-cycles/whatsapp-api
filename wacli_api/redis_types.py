"""Typed protocol for the sync Redis client interface used by this service.

redis-py's own stubs leave blocking operations typed as ``Awaitable[X] | X``
and do not support the ``Redis[str]`` generic.  This Protocol captures the
exact subset of methods this service uses, with the correct sync return types.
"""

from __future__ import annotations

from typing import Protocol


class RedisClient(Protocol):
    """Structural interface for the redis.Redis methods used by this service."""

    def ping(self) -> bool:
        """Return True if the server is alive."""
        ...

    def lpush(self, name: str, *values: str | bytes) -> int:
        """Prepend values to a list; return the new length."""
        ...

    def blpop(
        self, keys: str | list[str], timeout: int | float = 0
    ) -> list[str] | None:
        """Block-pop from list head; return [key, value] or None on timeout."""
        ...

    def brpop(
        self, keys: str | list[str], timeout: int | float = 0
    ) -> list[str] | None:
        """Block-pop from list tail; return [key, value] or None on timeout."""
        ...

    def expire(self, name: str, time: int) -> bool:
        """Set TTL on key; return True if key exists and TTL was set."""
        ...

    def close(self) -> None:
        """Close all connections in the pool."""
        ...
