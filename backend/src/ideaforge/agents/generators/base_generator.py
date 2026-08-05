from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from ideaforge.agents.base import BaseAgent
from ideaforge.agents.schemas import GeneratorOutput

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


class BaseGeneratorAgent(BaseAgent):
    def __init__(
        self,
        api_key: str,
        model: str,
        persona: str,
        style_guide: str,
    ) -> None:
        _llm = ChatGoogleGenerativeAI(
            google_api_key=api_key,
            model=model,
            temperature=0.9,
            request_timeout=180,
        )
        self._chain = _PROMPT | _llm.with_structured_output(GeneratorOutput)
        self._persona = persona
        self._style_guide = style_guide

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
                "persona": self._persona,
                "style_guide": self._style_guide,
                "problem": problem,
                "web_section": web_section,
                "rag_section": rag_section,
            },
        )
