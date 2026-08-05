import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ideaforge.domain.enums import JudgeType


class EvaluationCreate(BaseModel):
    idea_id: uuid.UUID
    judge_type: JudgeType
    score: float = Field(..., ge=0.0, le=10.0)
    strengths: list[str] | None = None
    weaknesses: list[str] | None = None
    recommendations: list[str] | None = None


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    idea_id: uuid.UUID
    judge_type: str
    score: float
    strengths: list[str] | None
    weaknesses: list[str] | None
    recommendations: list[str] | None
    created_at: datetime
