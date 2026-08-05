import uuid

import pytest

from ideaforge.api.schemas.idea import IdeaCreate
from ideaforge.api.schemas.project import ProjectCreate
from ideaforge.api.schemas.report import ReportCreate
from ideaforge.api.schemas.user import UserCreate
from ideaforge.infrastructure.repositories.idea_repository import SQLIdeaRepository
from ideaforge.infrastructure.repositories.project_repository import SQLProjectRepository
from ideaforge.infrastructure.repositories.report_repository import SQLReportRepository
from ideaforge.infrastructure.repositories.user_repository import SQLUserRepository

SAMPLE_MARKDOWN = """
# IdeaForge Final Report

## Winning Idea: AI Tutor

### Why It Won
Strong market demand with clear monetization.

### Risks
- Competition from large edtech players

### MVP Scope
- Basic tutoring module
- User authentication
"""


@pytest.fixture
async def project_with_idea(
    user_repo: SQLUserRepository,
    project_repo: SQLProjectRepository,
    idea_repo: SQLIdeaRepository,
):
    user = await user_repo.create(UserCreate(name="Tester", email=f"{uuid.uuid4()}@test.com"))
    project = await project_repo.create(
        ProjectCreate(
            user_id=user.id,
            title="Report Test Project",
            problem_statement="A valid problem statement",
        )
    )
    idea = await idea_repo.create(
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
    return project, idea


@pytest.mark.asyncio
async def test_create_report(
    report_repo: SQLReportRepository, project_with_idea
) -> None:
    project, idea = project_with_idea
    report = await report_repo.create(
        ReportCreate(
            project_id=project.id,
            winner_idea_id=idea.id,
            markdown_report=SAMPLE_MARKDOWN,
        )
    )

    assert report.id is not None
    assert report.project_id == project.id
    assert report.winner_idea_id == idea.id
    assert report.markdown_report == SAMPLE_MARKDOWN
    assert report.created_at is not None


@pytest.mark.asyncio
async def test_get_by_project(
    report_repo: SQLReportRepository, project_with_idea
) -> None:
    project, idea = project_with_idea
    await report_repo.create(
        ReportCreate(
            project_id=project.id,
            winner_idea_id=idea.id,
            markdown_report=SAMPLE_MARKDOWN,
        )
    )
    found = await report_repo.get_by_project(project.id)

    assert found is not None
    assert found.project_id == project.id


@pytest.mark.asyncio
async def test_get_by_project_not_found(report_repo: SQLReportRepository) -> None:
    result = await report_repo.get_by_project(uuid.uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_create_report_without_winner(
    report_repo: SQLReportRepository, project_with_idea
) -> None:
    project, _ = project_with_idea
    report = await report_repo.create(
        ReportCreate(
            project_id=project.id,
            markdown_report="Partial report — winner not determined yet.",
        )
    )
    assert report.winner_idea_id is None


@pytest.mark.asyncio
async def test_delete_report(
    report_repo: SQLReportRepository, project_with_idea
) -> None:
    project, idea = project_with_idea
    report = await report_repo.create(
        ReportCreate(
            project_id=project.id,
            winner_idea_id=idea.id,
            markdown_report=SAMPLE_MARKDOWN,
        )
    )
    deleted = await report_repo.delete(report.id)

    assert deleted is True
    assert await report_repo.get_by_id(report.id) is None
