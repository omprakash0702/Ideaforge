import uuid

import structlog

from ideaforge.core.exceptions import WorkflowError
from ideaforge.domain.enums import ProjectStatus
from ideaforge.infrastructure.database.postgres import AsyncSessionLocal
from ideaforge.infrastructure.repositories.project_repository import SQLProjectRepository
from ideaforge.workflow.deps import WorkflowDeps
from ideaforge.workflow.graph import build_workflow

logger = structlog.get_logger(__name__)


class WorkflowService:
    """Runs the compiled LangGraph workflow as a background task."""

    def __init__(self, deps: WorkflowDeps) -> None:
        self._deps = deps
        self._workflow = build_workflow(deps)

    async def run(self, project_id: str, problem_statement: str) -> None:
        """Execute the full IdeaForge pipeline.

        Designed to be called via FastAPI BackgroundTasks — manages its own
        DB sessions and catches all errors to mark the project FAILED.
        """
        logger.info("workflow.start", project_id=project_id)
        try:
            await self._workflow.ainvoke(
                {
                    "project_id": project_id,
                    "problem_statement": problem_statement,
                }
            )
            logger.info("workflow.complete", project_id=project_id)
        except WorkflowError as exc:
            logger.error("workflow.error", project_id=project_id, error=str(exc))
            await self._mark_failed(project_id)
        except Exception as exc:
            logger.error("workflow.unexpected_error", project_id=project_id, error=str(exc))
            await self._mark_failed(project_id)

    async def _mark_failed(self, project_id: str) -> None:
        try:
            async with AsyncSessionLocal() as session:
                repo = SQLProjectRepository(session)
                await repo.update_status(uuid.UUID(project_id), ProjectStatus.FAILED)
                await session.commit()
        except Exception as exc:
            logger.error("workflow.mark_failed_error", project_id=project_id, error=str(exc))
