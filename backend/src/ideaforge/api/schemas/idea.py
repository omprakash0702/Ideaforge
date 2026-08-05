import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ideaforge.domain.enums import GeneratorType


class IdeaCreate(BaseModel):
    project_id: uuid.UUID
    parent_idea_id: uuid.UUID | None = None
    version: int = Field(default=1, ge=1, le=4)
    generator_type: GeneratorType | None = None

    # Core agent schema fields (02_Agent_Design.md)
    title: str = Field(..., min_length=1, max_length=500)
    problem: str = Field(..., min_length=1)
    solution: str = Field(..., min_length=1)
    target_audience: str = Field(..., min_length=1)
    business_model: str = Field(..., min_length=1)
    tech_stack: str = Field(..., min_length=1)
    key_features: list[str] | None = None
    competitors: list[str] | None = None


class IdeaUpdate(BaseModel):
    score: float | None = Field(default=None, ge=0.0, le=100.0)
    is_winner: bool | None = None
    # Evolution may update core fields
    title: str | None = Field(default=None, min_length=1, max_length=500)
    problem: str | None = None
    solution: str | None = None
    target_audience: str | None = None
    business_model: str | None = None
    tech_stack: str | None = None
    key_features: list[str] | None = None


class UserIdeaCreate(BaseModel):
    """Body for user-submitted ideas (POST /projects/{id}/ideas)."""
    title: str = Field(..., min_length=1, max_length=500)
    problem: str = Field(..., min_length=1)
    solution: str = Field(..., min_length=1)
    target_audience: str = Field(..., min_length=1)
    business_model: str = Field(..., min_length=1)
    tech_stack: str = Field(..., min_length=1)
    key_features: list[str] | None = None
    competitors: list[str] | None = None


class ConstrainedGenerateRequest(BaseModel):
    """Body for constrained idea generation (POST /projects/{id}/ideas/generate)."""
    constraints: str = Field(..., min_length=1, max_length=2000)


# ── Graph response types ──────────────────────────────────────────────────────

class IdeaGraphNode(BaseModel):
    id: str
    title: str
    project_id: str
    version: int = 1
    generator_type: str | None = None
    # Full idea content
    problem: str = ""
    solution: str = ""
    target_audience: str = ""
    business_model: str = ""
    tech_stack: str = ""
    key_features: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    # Tournament metadata
    tournament_rank: int | None = None
    aggregate_score: float | None = None
    is_winner: bool = False


class IdeaGraphEdge(BaseModel):
    source: str
    target: str
    type: str  # "EVOLVED_INTO" | "RANKED_ABOVE"
    # EVOLVED_INTO metadata
    evolution_rationale: str | None = None
    score_before: float | None = None
    score_after: float | None = None
    score_delta: float | None = None
    # RANKED_ABOVE metadata
    score_diff: float | None = None


class JudgeNode(BaseModel):
    id: str
    judge_type: str  # INVESTOR | ENGINEER | SKEPTIC
    project_id: str


class EvaluationEdge(BaseModel):
    source: str   # judge node id
    target: str   # idea node id
    score: float
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class IdeaGraphResponse(BaseModel):
    nodes: list[IdeaGraphNode]
    edges: list[IdeaGraphEdge]            # EVOLVED_INTO + RANKED_ABOVE
    judge_nodes: list[JudgeNode] = Field(default_factory=list)
    evaluation_edges: list[EvaluationEdge] = Field(default_factory=list)


# ── REST response ─────────────────────────────────────────────────────────────

class IdeaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    parent_idea_id: uuid.UUID | None
    version: int
    generator_type: str | None
    title: str
    problem: str
    solution: str
    target_audience: str
    business_model: str
    tech_stack: str
    key_features: list[str] | None
    competitors: list[str] | None
    score: float | None
    is_winner: bool
    created_at: datetime
    updated_at: datetime
