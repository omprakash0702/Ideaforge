from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ideaforge.core.config import get_settings
from ideaforge.core.logging import setup_logging
from ideaforge.infrastructure.database.neo4j import close_neo4j_driver
from ideaforge.infrastructure.database.postgres import engine
from ideaforge.infrastructure.cache.redis import close_redis_client
from ideaforge.api.v1 import v1_router

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    setup_logging(debug=settings.debug, environment=settings.environment)

    # LangSmith tracing — auto-detected by LangChain when env vars are set.
    # Set LANGSMITH_TRACING=true and LANGSMITH_API_KEY to enable.
    if settings.langsmith_tracing and settings.langsmith_api_key:
        import os
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        os.environ.setdefault("LANGCHAIN_API_KEY", settings.langsmith_api_key)
        logger.info("langsmith.enabled")

    logger.info(
        "IdeaForge starting",
        version=settings.app_version,
        environment=settings.environment,
    )

    # All connections are lazy — no eager connect here.
    # /health/ready is the authoritative connectivity probe.

    yield

    logger.info("IdeaForge shutting down")
    await close_redis_client()
    await close_neo4j_driver()
    await engine.dispose()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.allowed_origins.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    app.include_router(v1_router)

    return app


app = create_app()
