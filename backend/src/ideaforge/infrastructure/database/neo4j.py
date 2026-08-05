from neo4j import AsyncDriver, AsyncGraphDatabase

from ideaforge.core.config import get_settings

# Module-level singleton — shared across all requests.
# Opened lazily on first call to get_neo4j_driver().
_driver: AsyncDriver | None = None


async def get_neo4j_driver() -> AsyncDriver:
    """FastAPI dependency that returns the shared async Neo4j driver.

    The driver is thread-safe and manages its own internal connection pool.
    Do NOT close it between requests — call close_neo4j_driver() on shutdown.
    """
    global _driver
    if _driver is None:
        settings = get_settings()
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
        )
    return _driver


async def close_neo4j_driver() -> None:
    """Gracefully close the driver on application shutdown."""
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None
