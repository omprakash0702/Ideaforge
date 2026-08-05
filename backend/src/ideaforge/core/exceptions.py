class IdeaForgeError(Exception):
    """Base exception for all IdeaForge domain errors."""


class NotFoundError(IdeaForgeError):
    """Raised when a requested resource does not exist."""


class ConflictError(IdeaForgeError):
    """Raised when an operation conflicts with current state (e.g. wrong project status)."""


class WorkflowError(IdeaForgeError):
    """Raised when the LangGraph workflow encounters an unrecoverable error."""


class AgentError(IdeaForgeError):
    """Raised when an AI agent fails after all retries are exhausted."""


class AgentOutputError(IdeaForgeError):
    """Raised when agent output does not conform to the expected Pydantic schema."""


class GuardrailViolationError(IdeaForgeError):
    """Raised when input fails content moderation.

    Attributes:
        category: ViolationCategory value (e.g. 'HATE_SPEECH')
        reason:   Human-readable explanation for the rejection
    """

    def __init__(self, category: str, reason: str) -> None:
        self.category = category
        self.reason = reason
        super().__init__(f"Content rejected [{category}]: {reason}")
