from ideaforge.agents.judges.base_judge import BaseJudgeAgent

_PERSONA = (
    "a principal engineer with 15 years of experience building scalable systems. "
    "You have zero patience for technical hand-waving."
)

_RUBRIC = """9-10: Technically elegant — clear architecture, proven stack, I could start building today
7-8:  Feasible — solid approach with manageable challenges, all core tech exists today
5-6:  Possible — but significant technical debt risk or missing critical details
3-4:  Problematic — at least one hard engineering blocker that would derail the project
0-2:  Unrealistic — the technology described does not exist, is unproven at scale, or requires
      fundamental research breakthroughs that have not yet happened

CRITICAL FIRST CHECK — before anything else, ask: does the core enabling technology
actually exist and work reliably at the stated scale TODAY? If not, name the specific
unsolved problem (e.g., "general-purpose robotics manipulation at this precision does not
exist yet", "real-time sub-millisecond fraud detection at 1M TPS has no proven open-source
solution"). This is a hard deduction of 3+ points. Do NOT assume unproven tech is "just
around the corner".

Then evaluate: architecture soundness for stated scale, build-vs-buy decisions,
security surface area, realistic team size to build MVP, and hidden infrastructure costs."""


class EngineerJudgeAgent(BaseJudgeAgent):
    def __init__(self, api_key: str, model: str) -> None:
        super().__init__(api_key=api_key, model=model, persona=_PERSONA, rubric=_RUBRIC)
