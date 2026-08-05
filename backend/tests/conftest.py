import pytest
from httpx import ASGITransport, AsyncClient

from ideaforge.main import app


@pytest.fixture
async def client() -> AsyncClient:
    """Async test client wired to the FastAPI app.

    Uses ASGITransport so no real network socket is opened.
    The lifespan is NOT triggered — no DB connections are made.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
