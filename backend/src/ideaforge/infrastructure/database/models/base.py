import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key generated on the Python side.

    Generating IDs in Python (not via gen_random_uuid()) means the caller
    knows the ID before the INSERT, which simplifies service orchestration.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """created_at only — for immutable records (User, Evaluation, Report)."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class UpdatedAtMixin(TimestampMixin):
    """created_at + updated_at — for mutable records (Project, Idea).

    updated_at uses a Python-side callable so the ORM injects the value
    into every UPDATE SET clause without requiring a PostgreSQL trigger.
    """

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=_utcnow,
        nullable=False,
    )
