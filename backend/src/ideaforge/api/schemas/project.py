import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ideaforge.domain.enums import ProjectStatus


class ProjectCreate(BaseModel):
    user_id: uuid.UUID
    title: str = Field(..., min_length=1, max_length=255)
    problem_statement: str = Field(..., min_length=10)


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    status: ProjectStatus | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    problem_statement: str
    status: str
    created_at: datetime
    updated_at: datetime
