# Re-export models so that a single import registers all of them
# with SQLAlchemy's mapper registry and Alembic's metadata.
from ideaforge.infrastructure.database.models import (  # noqa: F401
    User,
    Project,
    Idea,
    Evaluation,
    Report,
)
