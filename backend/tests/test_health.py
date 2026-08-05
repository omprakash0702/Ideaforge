import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_liveness_returns_200(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_liveness_has_no_component_checks(client: AsyncClient) -> None:
    """Liveness must not contact any external service."""
    response = await client.get("/api/v1/health")

    assert response.json()["components"] == {}


@pytest.mark.asyncio
async def test_liveness_includes_environment(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert "environment" in response.json()
