import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ideaforge.infrastructure.database.models.evaluation import Evaluation
from ideaforge.infrastructure.database.models.idea import Idea
from ideaforge.api.schemas.evaluation import EvaluationCreate


class SQLEvaluationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: EvaluationCreate) -> Evaluation:
        evaluation = Evaluation(**data.model_dump())
        self._session.add(evaluation)
        await self._session.flush()
        await self._session.refresh(evaluation)
        return evaluation

    async def create_bulk(self, data: list[EvaluationCreate]) -> list[Evaluation]:
        """Insert all evaluations in a single flush for efficiency."""
        evaluations = [Evaluation(**item.model_dump()) for item in data]
        self._session.add_all(evaluations)
        await self._session.flush()
        for ev in evaluations:
            await self._session.refresh(ev)
        return evaluations

    async def get_by_id(self, evaluation_id: uuid.UUID) -> Evaluation | None:
        result = await self._session.execute(
            select(Evaluation).where(Evaluation.id == evaluation_id)
        )
        return result.scalar_one_or_none()

    async def list_by_idea(self, idea_id: uuid.UUID) -> list[Evaluation]:
        result = await self._session.execute(
            select(Evaluation)
            .where(Evaluation.idea_id == idea_id)
            .order_by(Evaluation.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_by_project(self, project_id: uuid.UUID) -> list[Evaluation]:
        """Fetch all evaluations for every idea in a project in one query."""
        result = await self._session.execute(
            select(Evaluation)
            .join(Idea, Evaluation.idea_id == Idea.id)
            .where(Idea.project_id == project_id)
            .order_by(Evaluation.created_at.asc())
        )
        return list(result.scalars().all())

    async def delete(self, evaluation_id: uuid.UUID) -> bool:
        evaluation = await self.get_by_id(evaluation_id)
        if evaluation is None:
            return False
        await self._session.delete(evaluation)
        await self._session.flush()
        return True
