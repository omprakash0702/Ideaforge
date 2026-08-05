from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ideaforge.infrastructure.database.models.project import Project
    from ideaforge.api.schemas.project import ProjectCreate
    from ideaforge.domain.enums import ProjectStatus


class IProjectRepository(Protocol):
    async def create(self, data: ProjectCreate) -> Project: ...

    async def get_by_id(self, project_id: uuid.UUID) -> Project | None: ...

    async def list_by_user(self, user_id: uuid.UUID) -> list[Project]: ...

    async def update_status(
        self, project_id: uuid.UUID, status: ProjectStatus
    ) -> Project | None: ...

    async def delete(self, project_id: uuid.UUID) -> bool: ...
