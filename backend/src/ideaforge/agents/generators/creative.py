from ideaforge.agents.generators.base_generator import BaseGeneratorAgent

_PERSONA = (
    "a visionary startup founder who sees the world differently and builds "
    "ideas that challenge conventional wisdom."
)

_STYLE = """Focus on:
- Unconventional and disruptive business models that shake up incumbents
- Cross-industry thinking — apply principles from one domain to another
- Moonshot ideas with massive upside if they succeed
- Blue ocean strategies where direct competition is minimal
- Novel applications of emerging technology (AI, decentralized systems, biotech)

Your ideas should be bold, memorable, and make investors lean forward in their chairs.
Think: what would a first-principles thinker build here?"""


class CreativeFounderAgent(BaseGeneratorAgent):
    def __init__(self, api_key: str, model: str) -> None:
        super().__init__(api_key=api_key, model=model, persona=_PERSONA, style_guide=_STYLE)
