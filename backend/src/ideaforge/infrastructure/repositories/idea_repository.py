import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ideaforge.infrastructure.database.models.idea import Idea
from ideaforge.api.schemas.idea import IdeaCreate, IdeaUpdate


class SQLIdeaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: IdeaCreate) -> Idea:
        idea = Idea(**data.model_dump())
        self._session.add(idea)
        await self._session.flush()
        await self._session.refresh(idea)
        return idea

    async def get_by_id(self, idea_id: uuid.UUID) -> Idea | None:
        result = await self._session.execute(
            select(Idea).where(Idea.id == idea_id)
        )
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: uuid.UUID) -> list[Idea]:
        result = await self._session.execute(
            select(Idea)
            .where(Idea.project_id == project_id)
            .order_by(Idea.version.asc(), Idea.created_at.asc())
        )
        return list(result.scalars().all())

    async def update(self, idea_id: uuid.UUID, data: IdeaUpdate) -> Idea | None:
        idea = await self.get_by_id(idea_id)
        if idea is None:
            return None
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(idea, field, value)
        await self._session.flush()
        await self._session.refresh(idea)
        return idea

    async def mark_winner(self, idea_id: uuid.UUID) -> Idea | None:
        """Mark one idea as winner and clear winner flag on all siblings."""
        idea = await self.get_by_id(idea_id)
        if idea is None:
            return None

        # Clear any existing winner in this project (Core UPDATE)
        await self._session.execute(
            update(Idea)
            .where(Idea.project_id == idea.project_id)
            .values(is_winner=False)
        )
        # Expire ORM identity map so the next attribute access re-reads from DB
        # instead of using the pre-UPDATE in-memory state (stale is_winner=True).
        self._session.expire(idea)
        idea.is_winner = True
        await self._session.flush()
        await self._session.refresh(idea)
        return idea

    async def get_evolution_chain(self, idea_id: uuid.UUID) -> list[Idea]:
        """Return the full lineage: original idea → ... → given idea_id.

        Walks parent_idea_id links iteratively. Maximum chain depth = 4
        (matches the versioning strategy in 03_Data_Model.md).
        """
        chain: list[Idea] = []
        current_id: uuid.UUID | None = idea_id

        while current_id is not None and len(chain) < 4:
            idea = await self.get_by_id(current_id)
            if idea is None:
                break
            chain.insert(0, idea)
            current_id = idea.parent_idea_id

        return chain

    async def delete(self, idea_id: uuid.UUID) -> bool:
        idea = await self.get_by_id(idea_id)
        if idea is None:
            return False
        await self._session.delete(idea)
        await self._session.flush()
        return True
