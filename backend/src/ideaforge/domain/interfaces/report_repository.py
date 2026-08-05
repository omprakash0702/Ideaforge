from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ideaforge.infrastructure.database.models.report import Report
    from ideaforge.api.schemas.report import ReportCreate


class IReportRepository(Protocol):
    async def create(self, data: ReportCreate) -> Report: ...

    async def get_by_id(self, report_id: uuid.UUID) -> Report | None: ...

    async def get_by_project(self, project_id: uuid.UUID) -> Report | None: ...

    async def delete(self, report_id: uuid.UUID) -> bool: ...
