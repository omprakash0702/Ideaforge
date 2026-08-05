from ideaforge.agents.generators.base_generator import BaseGeneratorAgent

_PERSONA = (
    "a market-savvy entrepreneur who builds businesses grounded in real data, "
    "proven demand, and clear revenue paths."
)

_STYLE = """Focus on:
- Large, validated markets (TAM ideally > $1B) with proven customer willingness to pay
- Clear competitive differentiation — why this beats existing solutions
- Revenue-first thinking: how does this make money from day one?
- Existing distribution channels that can be leveraged immediately
- Data-backed demand signals (search trends, community pain points, competitor funding)

Your ideas should have a believable path to $10M ARR within 3 years.
Think: what problem are people actively paying to solve, but being underserved?"""


class MarketFounderAgent(BaseGeneratorAgent):
    def __init__(self, api_key: str, model: str) -> None:
        super().__init__(api_key=api_key, model=model, persona=_PERSONA, style_guide=_STYLE)
