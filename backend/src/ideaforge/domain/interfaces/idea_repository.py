from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ideaforge.infrastructure.database.models.idea import Idea
    from ideaforge.api.schemas.idea import IdeaCreate, IdeaUpdate


class IIdeaRepository(Protocol):
    async def create(self, data: IdeaCreate) -> Idea: ...

    async def get_by_id(self, idea_id: uuid.UUID) -> Idea | None: ...

    async def list_by_project(self, project_id: uuid.UUID) -> list[Idea]: ...

    async def update(self, idea_id: uuid.UUID, data: IdeaUpdate) -> Idea | None: ...

    async def mark_winner(self, idea_id: uuid.UUID) -> Idea | None: ...

    async def get_evolution_chain(self, idea_id: uuid.UUID) -> list[Idea]: ...

    async def delete(self, idea_id: uuid.UUID) -> bool: ...
