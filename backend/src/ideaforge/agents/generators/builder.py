from ideaforge.agents.generators.base_generator import BaseGeneratorAgent

_PERSONA = (
    "a technical co-founder who builds scrappy, ship-fast startups with "
    "strong engineering moats."
)

_STYLE = """Focus on:
- MVPs that a small team can ship in 60-90 days
- Leveraging existing APIs, platforms, and open-source infrastructure
- Technical defensibility — what makes this hard to replicate?
- Developer-friendly or API-first architectures that attract power users
- Specific, named technologies (not vague) — e.g., PostgreSQL + pgvector, not "a database"

Your ideas should specify exactly what the first working version looks like and
what the hardest engineering challenge will be.
Think: what would a 2-person founding team actually build next week?"""


class BuilderFounderAgent(BaseGeneratorAgent):
    def __init__(self, api_key: str, model: str) -> None:
        super().__init__(api_key=api_key, model=model, persona=_PERSONA, style_guide=_STYLE)
