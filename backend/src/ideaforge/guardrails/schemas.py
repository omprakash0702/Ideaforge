import enum

from pydantic import BaseModel, Field


class ViolationCategory(str, enum.Enum):
    SAFE = "SAFE"
    AMBIGUOUS = "AMBIGUOUS"           # vague monetization / purpose unclear — needs user clarification
    HATE_SPEECH = "HATE_SPEECH"       # slurs, discrimination, targeting groups
    ILLEGAL_ACTIVITY = "ILLEGAL_ACTIVITY"  # drug trade, weapons, fraud, hacking
    HARMFUL = "HARMFUL"               # ideas that endanger people
    DEROGATORY = "DEROGATORY"         # demeaning content not rising to hate speech
    EXPLICIT = "EXPLICIT"             # adult / sexually explicit
    SCAM = "SCAM"                     # pyramid schemes, MLM, predatory models


class GuardrailResult(BaseModel):
    """Result returned by the content guardrail for any text input."""

    safe: bool
    category: ViolationCategory = ViolationCategory.SAFE
    reason: str = Field(default="", description="Human-readable explanation when safe=False")
