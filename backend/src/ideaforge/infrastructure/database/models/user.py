from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ideaforge.infrastructure.database.postgres import Base
from ideaforge.infrastructure.database.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from ideaforge.infrastructure.database.models.project import Project


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # index=True creates an implicit index for email lookups
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    projects: Mapped[list[Project]] = relationship(
        "Project",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
