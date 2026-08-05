from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ideaforge.infrastructure.database.postgres import Base
from ideaforge.infrastructure.database.models.base import UpdatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from ideaforge.infrastructure.database.models.project import Project
    from ideaforge.infrastructure.database.models.evaluation import Evaluation


class Idea(Base, UUIDPrimaryKeyMixin, UpdatedAtMixin):
    __tablename__ = "ideas"
    __table_args__ = (
        Index("ix_ideas_project_id", "project_id"),
        Index("ix_ideas_parent_idea_id", "parent_idea_id"),
        # Composite index for fast "find winner of project" lookups
        Index("ix_ideas_project_winner", "project_id", "is_winner"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Self-referential FK for evolution lineage.
    # No ORM relationship defined here — full graph traversal belongs to Neo4j.
    parent_idea_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ideas.id", ondelete="SET NULL"),
        nullable=True,
    )

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # Which generator agent created this idea (CREATIVE / MARKET / BUILDER)
    generator_type: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # ── Core idea fields (mirrors shared agent schema in 02_Agent_Design.md) ──
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    problem: Mapped[str] = mapped_column(Text, nullable=False)
    solution: Mapped[str] = mapped_column(Text, nullable=False)
    target_audience: Mapped[str] = mapped_column(Text, nullable=False)
    business_model: Mapped[str] = mapped_column(Text, nullable=False)
    tech_stack: Mapped[str] = mapped_column(Text, nullable=False)
    key_features: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    competitors: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)

    # ── Scoring ──────────────────────────────────────────────────────────────
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_winner: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    project: Mapped[Project] = relationship("Project", back_populates="ideas")
    evaluations: Mapped[list[Evaluation]] = relationship(
        "Evaluation",
        back_populates="idea",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Idea id={self.id} title={self.title!r} v{self.version}>"
