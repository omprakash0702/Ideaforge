from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from ideaforge.api.dependencies import DBSession, Neo4jDriver
from ideaforge.core.config import get_settings

router = APIRouter(prefix="/health", tags=["health"])


class ComponentHealth(BaseModel):
    status: str
    message: str = ""


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    components: dict[str, ComponentHealth] = {}


@router.get("", response_model=HealthResponse, summary="Liveness check")
async def liveness() -> HealthResponse:
    """Confirms the process is alive. Does not contact any external service."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/ready", response_model=HealthResponse, summary="Readiness check")
async def readiness(db: DBSession, neo4j: Neo4jDriver) -> HealthResponse:
    """Probes PostgreSQL and Neo4j connectivity. Returns 200 only when both are reachable."""
    settings = get_settings()
    components: dict[str, ComponentHealth] = {}
    overall = "healthy"

    # PostgreSQL
    try:
        await db.execute(text("SELECT 1"))
        components["postgres"] = ComponentHealth(status="healthy", message="Connected")
    except Exception as exc:
        components["postgres"] = ComponentHealth(status="unhealthy", message=str(exc))
        overall = "unhealthy"

    # Neo4j
    try:
        await neo4j.verify_connectivity()
        components["neo4j"] = ComponentHealth(status="healthy", message="Connected")
    except Exception as exc:
        components["neo4j"] = ComponentHealth(status="unhealthy", message=str(exc))
        overall = "unhealthy"

    return HealthResponse(
        status=overall,
        version=settings.app_version,
        environment=settings.environment,
        components=components,
    )
