import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ideaforge.infrastructure.database.models.project import Project
from ideaforge.api.schemas.project import ProjectCreate
from ideaforge.domain.enums import ProjectStatus


class SQLProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: ProjectCreate) -> Project:
        project = Project(**data.model_dump())
        self._session.add(project)
        await self._session.flush()
        await self._session.refresh(project)
        return project

    async def get_by_id(self, project_id: uuid.UUID) -> Project | None:
        result = await self._session.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: uuid.UUID) -> list[Project]:
        result = await self._session.execute(
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(
        self, project_id: uuid.UUID, status: ProjectStatus
    ) -> Project | None:
        project = await self.get_by_id(project_id)
        if project is None:
            return None
        project.status = status.value
        await self._session.flush()
        await self._session.refresh(project)
        return project

    async def update_status_if_in(
        self,
        project_id: uuid.UUID,
        from_statuses: set[str],
        to_status: ProjectStatus,
    ) -> Project | None:
        """Atomic compare-and-swap: transition only when current status is in from_statuses.

        Issues a single UPDATE WHERE status IN (...) so concurrent callers cannot
        both succeed — only the first writer wins; the second gets None back.
        """
        result = await self._session.execute(
            update(Project)
            .where(Project.id == project_id, Project.status.in_(from_statuses))
            .values(status=to_status.value)
            .returning(Project)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        await self._session.flush()
        return row

    async def delete(self, project_id: uuid.UUID) -> bool:
        project = await self.get_by_id(project_id)
        if project is None:
            return False
        await self._session.delete(project)
        await self._session.flush()
        return True
