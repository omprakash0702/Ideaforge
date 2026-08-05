from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from ideaforge.agents.base import BaseAgent
from ideaforge.agents.schemas import GeneratorOutput

_PERSONA = (
    "a data-driven startup founder who builds ideas from evidence, "
    "market signals, and measurable user pain points — not intuition."
)

_STYLE = """Focus on:
- Quantifiable market problems: cite why the pain is large and measurable
- Business models with clear unit economics and low CAC/high LTV potential
- Defensibility through data moats, network effects, or switching costs
- Adjacent markets and underserved verticals where incumbents have blind spots
- Metrics-first product thinking: North Star metrics defined from day one

Your ideas should be grounded, specific, and backed by logical market reasoning.
Think: what would a McKinsey-trained founder who also codes build here?"""

_SYSTEM = """You are {persona}

Your task is to generate exactly 2 creative, viable startup ideas that address the given problem.
Each idea must be meaningfully distinct — different target audience, business model, or tech approach.

{style_guide}

Return EXACTLY 2 ideas. No more, no less."""

_HUMAN = """Problem Statement:
{problem}

{web_section}

{rag_section}

Generate 2 startup ideas now."""

_PROMPT = ChatPromptTemplate.from_messages([("system", _SYSTEM), ("human", _HUMAN)])


class AnalystFounderAgent(BaseAgent):
    _invoke_timeout = 120.0

    def __init__(self, api_key: str, model: str) -> None:
        _llm = ChatOpenAI(api_key=api_key, model=model, temperature=0.7, timeout=120)
        self._chain = _PROMPT | _llm.with_structured_output(GeneratorOutput)

    async def generate(
        self,
        problem: str,
        rag_context: str = "",
        web_context: str = "",
    ) -> GeneratorOutput:
        web_section = (
            f"Live market intelligence (web research):\n{web_context}"
            if web_context.strip()
            else ""
        )
        rag_section = (
            f"Relevant context from user's documents:\n{rag_context}"
            if rag_context.strip()
            else ""
        )
        return await self._invoke_with_retry(
            self._chain,
            {
                "persona": _PERSONA,
                "style_guide": _STYLE,
                "problem": problem,
                "web_section": web_section,
                "rag_section": rag_section,
            },
        )
