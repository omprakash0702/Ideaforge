import uuid

import pytest

from ideaforge.api.schemas.evaluation import EvaluationCreate
from ideaforge.api.schemas.idea import IdeaCreate
from ideaforge.api.schemas.project import ProjectCreate
from ideaforge.api.schemas.user import UserCreate
from ideaforge.domain.enums import JudgeType
from ideaforge.infrastructure.repositories.evaluation_repository import SQLEvaluationRepository
from ideaforge.infrastructure.repositories.idea_repository import SQLIdeaRepository
from ideaforge.infrastructure.repositories.project_repository import SQLProjectRepository
from ideaforge.infrastructure.repositories.user_repository import SQLUserRepository


@pytest.fixture
async def idea(
    user_repo: SQLUserRepository,
    project_repo: SQLProjectRepository,
    idea_repo: SQLIdeaRepository,
):
    user = await user_repo.create(UserCreate(name="Tester", email=f"{uuid.uuid4()}@test.com"))
    project = await project_repo.create(
        ProjectCreate(
            user_id=user.id,
            title="Eval Test",
            problem_statement="A valid problem statement",
        )
    )
    return await idea_repo.create(
        IdeaCreate(
            project_id=project.id,
            title="AI Tutor",
            problem="education gap",
            solution="AI tutoring",
            target_audience="students",
            business_model="SaaS",
            tech_stack="Python",
        )
    )


def _eval_data(idea_id: uuid.UUID, judge: JudgeType) -> EvaluationCreate:
    return EvaluationCreate(
        idea_id=idea_id,
        judge_type=judge,
        score=7.5,
        strengths=["clear problem", "scalable solution"],
        weaknesses=["competitive market"],
        recommendations=["focus on niche", "validate with users"],
    )


@pytest.mark.asyncio
async def test_create_evaluation(
    evaluation_repo: SQLEvaluationRepository, idea
) -> None:
    ev = await evaluation_repo.create(_eval_data(idea.id, JudgeType.INVESTOR))

    assert ev.id is not None
    assert ev.judge_type == JudgeType.INVESTOR.value
    assert ev.score == 7.5
    assert ev.strengths == ["clear problem", "scalable solution"]


@pytest.mark.asyncio
async def test_create_bulk(evaluation_repo: SQLEvaluationRepository, idea) -> None:
    bulk_data = [
        _eval_data(idea.id, JudgeType.INVESTOR),
        _eval_data(idea.id, JudgeType.ENGINEER),
        _eval_data(idea.id, JudgeType.SKEPTIC),
    ]
    evaluations = await evaluation_repo.create_bulk(bulk_data)

    assert len(evaluations) == 3
    judge_types = {ev.judge_type for ev in evaluations}
    assert judge_types == {JudgeType.INVESTOR.value, JudgeType.ENGINEER.value, JudgeType.SKEPTIC.value}


@pytest.mark.asyncio
async def test_list_by_idea(evaluation_repo: SQLEvaluationRepository, idea) -> None:
    await evaluation_repo.create(_eval_data(idea.id, JudgeType.INVESTOR))
    await evaluation_repo.create(_eval_data(idea.id, JudgeType.ENGINEER))

    evaluations = await evaluation_repo.list_by_idea(idea.id)
    assert len(evaluations) == 2


@pytest.mark.asyncio
async def test_delete_evaluation(
    evaluation_repo: SQLEvaluationRepository, idea
) -> None:
    ev = await evaluation_repo.create(_eval_data(idea.id, JudgeType.SKEPTIC))
    deleted = await evaluation_repo.delete(ev.id)

    assert deleted is True
    assert await evaluation_repo.get_by_id(ev.id) is None


@pytest.mark.asyncio
async def test_delete_nonexistent(evaluation_repo: SQLEvaluationRepository) -> None:
    result = await evaluation_repo.delete(uuid.uuid4())
    assert result is False
