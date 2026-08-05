import uuid

import pytest

from ideaforge.api.schemas.project import ProjectCreate
from ideaforge.api.schemas.user import UserCreate
from ideaforge.domain.enums import ProjectStatus
from ideaforge.infrastructure.repositories.project_repository import SQLProjectRepository
from ideaforge.infrastructure.repositories.user_repository import SQLUserRepository


@pytest.fixture
async def user(user_repo: SQLUserRepository):
    return await user_repo.create(UserCreate(name="TestUser", email=f"{uuid.uuid4()}@test.com"))


@pytest.mark.asyncio
async def test_create_project(
    project_repo: SQLProjectRepository, user
) -> None:
    data = ProjectCreate(
        user_id=user.id,
        title="AI for Farmers",
        problem_statement="Help farmers improve crop yield using AI",
    )
    project = await project_repo.create(data)

    assert project.id is not None
    assert project.title == "AI for Farmers"
    assert project.status == ProjectStatus.CREATED.value
    assert project.updated_at is not None


@pytest.mark.asyncio
async def test_get_by_id(project_repo: SQLProjectRepository, user) -> None:
    project = await project_repo.create(
        ProjectCreate(
            user_id=user.id,
            title="Test Project",
            problem_statement="A test problem statement here",
        )
    )
    fetched = await project_repo.get_by_id(project.id)

    assert fetched is not None
    assert fetched.id == project.id


@pytest.mark.asyncio
async def test_get_by_id_not_found(project_repo: SQLProjectRepository) -> None:
    result = await project_repo.get_by_id(uuid.uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_list_by_user(project_repo: SQLProjectRepository, user) -> None:
    for i in range(3):
        await project_repo.create(
            ProjectCreate(
                user_id=user.id,
                title=f"Project {i}",
                problem_statement="A valid problem statement",
            )
        )
    projects = await project_repo.list_by_user(user.id)
    assert len(projects) >= 3


@pytest.mark.asyncio
async def test_update_status(project_repo: SQLProjectRepository, user) -> None:
    project = await project_repo.create(
        ProjectCreate(
            user_id=user.id,
            title="Status Test",
            problem_statement="A valid problem statement",
        )
    )
    updated = await project_repo.update_status(project.id, ProjectStatus.GENERATING)

    assert updated is not None
    assert updated.status == ProjectStatus.GENERATING.value


@pytest.mark.asyncio
async def test_update_status_not_found(project_repo: SQLProjectRepository) -> None:
    result = await project_repo.update_status(uuid.uuid4(), ProjectStatus.COMPLETED)
    assert result is None


@pytest.mark.asyncio
async def test_delete_project(project_repo: SQLProjectRepository, user) -> None:
    project = await project_repo.create(
        ProjectCreate(
            user_id=user.id,
            title="Delete Me",
            problem_statement="A valid problem statement",
        )
    )
    deleted = await project_repo.delete(project.id)

    assert deleted is True
    assert await project_repo.get_by_id(project.id) is None
