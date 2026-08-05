import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReportCreate(BaseModel):
    project_id: uuid.UUID
    winner_idea_id: uuid.UUID | None = None
    markdown_report: str = Field(..., min_length=1)


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    winner_idea_id: uuid.UUID | None
    markdown_report: str
    created_at: datetime
