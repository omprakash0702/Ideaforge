from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ideaforge.infrastructure.database.postgres import Base
from ideaforge.infrastructure.database.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from ideaforge.infrastructure.database.models.project import Project
    from ideaforge.infrastructure.database.models.idea import Idea


class Report(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "reports"
    __table_args__ = (
        # Enforces one report per project at the DB level
        UniqueConstraint("project_id", name="uq_reports_project_id"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Nullable: the winner may be cleared if an idea is deleted
    winner_idea_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ideas.id", ondelete="SET NULL"),
        nullable=True,
    )
    markdown_report: Mapped[str] = mapped_column(Text, nullable=False)

    project: Mapped[Project] = relationship("Project", back_populates="report")
    winner_idea: Mapped[Idea | None] = relationship("Idea")

    def __repr__(self) -> str:
        return f"<Report id={self.id} project_id={self.project_id}>"
