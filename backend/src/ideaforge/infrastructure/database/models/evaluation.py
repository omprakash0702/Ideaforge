from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Float, ForeignKey, Index, String, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ideaforge.infrastructure.database.postgres import Base
from ideaforge.infrastructure.database.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from ideaforge.infrastructure.database.models.idea import Idea


class Evaluation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "evaluations"
    __table_args__ = (
        Index("ix_evaluations_idea_id", "idea_id"),
        # One judge type can evaluate each idea only once
        UniqueConstraint("idea_id", "judge_type", name="uq_evaluation_idea_judge"),
    )

    idea_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ideas.id", ondelete="CASCADE"),
        nullable=False,
    )
    judge_type: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)

    # JSONB stores lists of strings produced by judge agents
    strengths: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    weaknesses: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    recommendations: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)

    idea: Mapped[Idea] = relationship("Idea", back_populates="evaluations")

    def __repr__(self) -> str:
        return f"<Evaluation id={self.id} judge={self.judge_type!r} score={self.score}>"
