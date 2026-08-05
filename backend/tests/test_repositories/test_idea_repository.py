import uuid

import pytest

from ideaforge.api.schemas.idea import IdeaCreate, IdeaUpdate
from ideaforge.api.schemas.project import ProjectCreate
from ideaforge.api.schemas.user import UserCreate
from ideaforge.domain.enums import GeneratorType
from ideaforge.infrastructure.repositories.idea_repository import SQLIdeaRepository
from ideaforge.infrastructure.repositories.project_repository import SQLProjectRepository
from ideaforge.infrastructure.repositories.user_repository import SQLUserRepository


@pytest.fixture
async def project(
    user_repo: SQLUserRepository, project_repo: SQLProjectRepository
):
    user = await user_repo.create(UserCreate(name="Tester", email=f"{uuid.uuid4()}@test.com"))
    return await project_repo.create(
        ProjectCreate(
            user_id=user.id,
            title="Idea Test Project",
            problem_statement="A valid problem statement for ideas",
        )
    )


def _idea_data(project_id: uuid.UUID, title: str = "Smart Crop Advisor") -> IdeaCreate:
    return IdeaCreate(
        project_id=project_id,
        version=1,
        generator_type=GeneratorType.CREATIVE,
        title=title,
        problem="Farmers lack data-driven insights",
        solution="AI-powered mobile advisory",
        target_audience="Small-scale farmers in India",
        business_model="SaaS subscription",
        tech_stack="Python, FastAPI, React Native",
        key_features=["crop yield prediction", "weather alerts", "market price updates"],
    )


@pytest.mark.asyncio
async def test_create_idea(idea_repo: SQLIdeaRepository, project) -> None:
    idea = await idea_repo.create(_idea_data(project.id))

    assert idea.id is not None
    assert idea.title == "Smart Crop Advisor"
    assert idea.version == 1
    assert idea.generator_type == GeneratorType.CREATIVE.value
    assert idea.key_features is not None
    assert idea.is_winner is False
    assert idea.score is None


@pytest.mark.asyncio
async def test_get_by_id(idea_repo: SQLIdeaRepository, project) -> None:
    idea = await idea_repo.create(_idea_data(project.id))
    fetched = await idea_repo.get_by_id(idea.id)

    assert fetched is not None
    assert fetched.id == idea.id


@pytest.mark.asyncio
async def test_list_by_project(idea_repo: SQLIdeaRepository, project) -> None:
    for i in range(3):
        await idea_repo.create(_idea_data(project.id, title=f"Idea {i}"))
    ideas = await idea_repo.list_by_project(project.id)

    assert len(ideas) == 3


@pytest.mark.asyncio
async def test_update_score(idea_repo: SQLIdeaRepository, project) -> None:
    idea = await idea_repo.create(_idea_data(project.id))
    updated = await idea_repo.update(idea.id, IdeaUpdate(score=78.5))

    assert updated is not None
    assert updated.score == 78.5


@pytest.mark.asyncio
async def test_mark_winner(idea_repo: SQLIdeaRepository, project) -> None:
    idea_a = await idea_repo.create(_idea_data(project.id, title="Idea A"))
    idea_b = await idea_repo.create(_idea_data(project.id, title="Idea B"))

    winner = await idea_repo.mark_winner(idea_a.id)
    assert winner is not None
    assert winner.is_winner is True

    # After marking A, B must not be a winner
    b_check = await idea_repo.get_by_id(idea_b.id)
    assert b_check is not None
    assert b_check.is_winner is False


@pytest.mark.asyncio
async def test_evolution_chain(idea_repo: SQLIdeaRepository, project) -> None:
    v1 = await idea_repo.create(_idea_data(project.id, title="V1 Idea"))
    v2 = await idea_repo.create(
        IdeaCreate(
            project_id=project.id,
            parent_idea_id=v1.id,
            version=2,
            title="V2 Idea",
            problem="p", solution="s", target_audience="t",
            business_model="b", tech_stack="ts",
        )
    )
    chain = await idea_repo.get_evolution_chain(v2.id)

    assert len(chain) == 2
    assert chain[0].id == v1.id
    assert chain[1].id == v2.id


@pytest.mark.asyncio
async def test_delete_idea(idea_repo: SQLIdeaRepository, project) -> None:
    idea = await idea_repo.create(_idea_data(project.id))
    deleted = await idea_repo.delete(idea.id)

    assert deleted is True
    assert await idea_repo.get_by_id(idea.id) is None
