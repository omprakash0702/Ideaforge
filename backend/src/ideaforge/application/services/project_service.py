import uuid

import structlog

from ideaforge.api.schemas.project import ProjectCreate
from ideaforge.core.exceptions import ConflictError, NotFoundError
from ideaforge.domain.enums import ProjectStatus
from ideaforge.infrastructure.database.models.project import Project
from ideaforge.infrastructure.repositories.idea_repository import SQLIdeaRepository
from ideaforge.infrastructure.repositories.project_repository import SQLProjectRepository
from ideaforge.infrastructure.repositories.report_repository import SQLReportRepository
from ideaforge.infrastructure.repositories.user_repository import SQLUserRepository

logger = structlog.get_logger(__name__)

_RUNNABLE_STATUSES = {ProjectStatus.CREATED.value, ProjectStatus.FAILED.value}


class ProjectService:
    def __init__(
        self,
        project_repo: SQLProjectRepository,
        user_repo: SQLUserRepository,
        idea_repo: SQLIdeaRepository,
        report_repo: SQLReportRepository,
    ) -> None:
        self._projects = project_repo
        self._users = user_repo
        self._ideas = idea_repo
        self._reports = report_repo

    async def create(self, data: ProjectCreate) -> Project:
        user = await self._users.get_by_id(data.user_id)
        if user is None:
            raise NotFoundError(f"User {data.user_id} not found")
        project = await self._projects.create(data)
        logger.info("project.created", project_id=str(project.id), user_id=str(data.user_id))
        return project

    async def get(self, project_id: uuid.UUID) -> Project:
        project = await self._projects.get_by_id(project_id)
        if project is None:
            raise NotFoundError(f"Project {project_id} not found")
        return project

    async def list_by_user(self, user_id: uuid.UUID) -> list[Project]:
        return await self._projects.list_by_user(user_id)

    async def mark_running(self, project_id: uuid.UUID) -> Project:
        """Transition project to GENERATING so the caller can launch the workflow.

        Uses an atomic UPDATE WHERE status IN (...) so concurrent POST /run
        requests cannot both succeed — only the first writer transitions the
        project; the second gets a ConflictError.
        """
        await self.get(project_id)  # raises NotFoundError if missing
        project = await self._projects.update_status_if_in(
            project_id,
            from_statuses=_RUNNABLE_STATUSES,
            to_status=ProjectStatus.GENERATING,
        )
        if project is None:
            raise ConflictError(
                f"Project {project_id} is already running or cannot be started. "
                f"Only {_RUNNABLE_STATUSES} projects can be started."
            )
        return project

    async def get_ideas(self, project_id: uuid.UUID) -> list:
        await self.get(project_id)  # raises NotFoundError if missing
        return await self._ideas.list_by_project(project_id)

    async def get_report(self, project_id: uuid.UUID):
        await self.get(project_id)
        report = await self._reports.get_by_project(project_id)
        if report is None:
            raise NotFoundError(f"No report yet for project {project_id}")
        return report
