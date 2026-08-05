"""Database fixtures for repository integration tests.

These tests require a running PostgreSQL instance. Start one with:

    docker compose up postgres -d

The test database (ideaforge_test) is created automatically by the session
fixture. Override TEST_DATABASE_URL in your environment if needed.
"""
import os

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Import all models so Base.metadata is populated before create_all
import ideaforge.infrastructure.database  # noqa: F401
from ideaforge.infrastructure.database.postgres import Base
from ideaforge.infrastructure.repositories.user_repository import SQLUserRepository
from ideaforge.infrastructure.repositories.project_repository import SQLProjectRepository
from ideaforge.infrastructure.repositories.idea_repository import SQLIdeaRepository
from ideaforge.infrastructure.repositories.evaluation_repository import SQLEvaluationRepository
from ideaforge.infrastructure.repositories.report_repository import SQLReportRepository

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/ideaforge_test",
)


@pytest.fixture(scope="session")
async def test_engine():
    """Create the test database schema once per test session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def session(test_engine) -> AsyncSession:
    """Yield a session bound to an open transaction.

    The transaction is rolled back after each test so the database is
    left in its initial state — no explicit cleanup needed in tests.
    """
    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        async with sess.begin():
            yield sess
            await sess.rollback()


# ── Repository fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def user_repo(session: AsyncSession) -> SQLUserRepository:
    return SQLUserRepository(session)


@pytest.fixture
def project_repo(session: AsyncSession) -> SQLProjectRepository:
    return SQLProjectRepository(session)


@pytest.fixture
def idea_repo(session: AsyncSession) -> SQLIdeaRepository:
    return SQLIdeaRepository(session)


@pytest.fixture
def evaluation_repo(session: AsyncSession) -> SQLEvaluationRepository:
    return SQLEvaluationRepository(session)


@pytest.fixture
def report_repo(session: AsyncSession) -> SQLReportRepository:
    return SQLReportRepository(session)
