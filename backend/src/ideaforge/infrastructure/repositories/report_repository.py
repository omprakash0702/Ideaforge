import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ideaforge.infrastructure.database.models.report import Report
from ideaforge.api.schemas.report import ReportCreate


class SQLReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: ReportCreate) -> Report:
        report = Report(**data.model_dump())
        self._session.add(report)
        await self._session.flush()
        await self._session.refresh(report)
        return report

    async def get_by_id(self, report_id: uuid.UUID) -> Report | None:
        result = await self._session.execute(
            select(Report).where(Report.id == report_id)
        )
        return result.scalar_one_or_none()

    async def get_by_project(self, project_id: uuid.UUID) -> Report | None:
        result = await self._session.execute(
            select(Report).where(Report.project_id == project_id)
        )
        return result.scalar_one_or_none()

    async def delete(self, report_id: uuid.UUID) -> bool:
        report = await self.get_by_id(report_id)
        if report is None:
            return False
        await self._session.delete(report)
        await self._session.flush()
        return True
