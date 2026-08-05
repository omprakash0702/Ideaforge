"""Pydantic schemas for structured agent inputs and outputs.

Every agent uses with_structured_output() — no plain-text parsing.
"""

from pydantic import BaseModel, Field


class IdeaSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    problem: str = Field(..., min_length=10)
    solution: str = Field(..., min_length=10)
    target_audience: str = Field(..., min_length=5)
    business_model: str = Field(..., min_length=5)
    tech_stack: str = Field(..., min_length=5)
    key_features: list[str] = Field(..., min_length=3, max_length=10)
    competitors: list[str] = Field(
        default_factory=list,
        min_length=2,
        max_length=6,
        description=(
            "2–5 real existing companies that compete in this space. "
            "Each entry: 'CompanyName — one-line positioning and key weakness vs this idea'"
        ),
    )


class GeneratorOutput(BaseModel):
    """Two distinct startup ideas from a single generator agent."""
    ideas: list[IdeaSchema] = Field(..., min_length=2, max_length=2)


class JudgmentSchema(BaseModel):
    """Score and rationale from one judge for one idea."""
    score: float = Field(..., ge=0.0, le=10.0)
    strengths: list[str] = Field(..., min_length=1)
    weaknesses: list[str] = Field(..., min_length=1)
    recommendations: list[str] = Field(..., min_length=1)


class EvolutionSchema(BaseModel):
    """Improved idea that directly addresses judge criticisms."""
    title: str = Field(..., min_length=1, max_length=200)
    problem: str = Field(..., min_length=10)
    solution: str = Field(..., min_length=10)
    target_audience: str = Field(..., min_length=5)
    business_model: str = Field(..., min_length=5)
    tech_stack: str = Field(..., min_length=5)
    key_features: list[str] = Field(..., min_length=3)
    evolution_rationale: str = Field(..., min_length=20,
                                     description="Brief explanation of what was changed and why.")


class ReportSchema(BaseModel):
    """Concise summary of the winning idea and why it won — no plans, no projections."""
    markdown_report: str = Field(
        ...,
        min_length=200,
        description=(
            "A short, honest Markdown summary covering: what the idea is, "
            "why it beat the others, what the judges agreed on, the real risks, "
            "and one concrete next step. No financial projections. No roadmaps. "
            "No org charts. Plain language only."
        ),
    )
