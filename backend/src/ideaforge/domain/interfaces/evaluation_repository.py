from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ideaforge.infrastructure.database.models.evaluation import Evaluation
    from ideaforge.api.schemas.evaluation import EvaluationCreate


class IEvaluationRepository(Protocol):
    async def create(self, data: EvaluationCreate) -> Evaluation: ...

    async def create_bulk(self, data: list[EvaluationCreate]) -> list[Evaluation]: ...

    async def get_by_id(self, evaluation_id: uuid.UUID) -> Evaluation | None: ...

    async def list_by_idea(self, idea_id: uuid.UUID) -> list[Evaluation]: ...

    async def list_by_project(self, project_id: uuid.UUID) -> list[Evaluation]: ...

    async def delete(self, evaluation_id: uuid.UUID) -> bool: ...
