from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ideaforge.infrastructure.database.postgres import Base
from ideaforge.infrastructure.database.models.base import UpdatedAtMixin, UUIDPrimaryKeyMixin
from ideaforge.domain.enums import ProjectStatus

if TYPE_CHECKING:
    from ideaforge.infrastructure.database.models.user import User
    from ideaforge.infrastructure.database.models.idea import Idea
    from ideaforge.infrastructure.database.models.report import Report


class Project(Base, UUIDPrimaryKeyMixin, UpdatedAtMixin):
    __tablename__ = "projects"
    __table_args__ = (
        Index("ix_projects_user_id", "user_id"),
        Index("ix_projects_status", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    problem_statement: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ProjectStatus.CREATED.value,
    )

    user: Mapped[User] = relationship("User", back_populates="projects")
    ideas: Mapped[list[Idea]] = relationship(
        "Idea",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    report: Mapped[Report | None] = relationship(
        "Report",
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} title={self.title!r} status={self.status!r}>"
