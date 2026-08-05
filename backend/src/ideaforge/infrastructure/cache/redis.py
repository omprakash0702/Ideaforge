import redis.asyncio as aioredis

from ideaforge.core.config import get_settings

# Module-level singleton — one connection pool shared across all requests.
# Opened lazily on first call to get_redis_client().
_client: aioredis.Redis | None = None


async def get_redis_client() -> aioredis.Redis:
    """Return the shared async Redis client.

    Uses from_url() which creates a connection pool automatically.
    hiredis (C extension) is used for response parsing when installed.

    Used for:
      - LangGraph workflow state checkpointing (Milestone 3)
      - LLM response caching (Milestones 4–8)
    """
    global _client
    if _client is None:
        settings = get_settings()
        _client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _client


async def close_redis_client() -> None:
    """Gracefully close the connection pool on application shutdown."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
