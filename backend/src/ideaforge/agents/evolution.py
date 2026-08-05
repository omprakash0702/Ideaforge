from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from ideaforge.agents.base import BaseAgent
from ideaforge.agents.schemas import EvolutionSchema

_SYSTEM = """You are a startup idea evolution engine. Your job is to take a startup idea
that scored poorly with expert judges and transform it into a significantly stronger version.

You must:
1. Directly address every weakness the judges identified
2. Preserve the core insight or value proposition (do not pivot to a completely different idea)
3. Incorporate specific recommendations where they make sense
4. Strengthen what judges praised as strengths
5. Be concrete — vague improvements are worthless

The evolved idea should be recognizably derived from the original but meaningfully better."""

_HUMAN = """Original Idea:
Title: {title}
Problem: {problem}
Solution: {solution}
Target Audience: {target_audience}
Business Model: {business_model}
Tech Stack: {tech_stack}
Key Features: {key_features}

Judge Feedback:
{feedback}

Evolve this idea into a stronger version that addresses the criticisms above."""

_PROMPT = ChatPromptTemplate.from_messages([("system", _SYSTEM), ("human", _HUMAN)])


class EvolutionAgent(BaseAgent):
    _invoke_timeout = 120.0

    def __init__(self, api_key: str, model: str) -> None:
        _llm = ChatOpenAI(api_key=api_key, model=model, temperature=0.3, timeout=120)
        self._chain = _PROMPT | _llm.with_structured_output(EvolutionSchema)

    async def evolve(self, idea: dict, evaluations: list[dict]) -> EvolutionSchema:
        feedback = _format_feedback(evaluations)
        return await self._invoke_with_retry(
            self._chain,
            {
                "title": idea.get("title", ""),
                "problem": idea.get("problem", ""),
                "solution": idea.get("solution", ""),
                "target_audience": idea.get("target_audience", ""),
                "business_model": idea.get("business_model", ""),
                "tech_stack": idea.get("tech_stack", ""),
                "key_features": ", ".join(idea.get("key_features") or []),
                "feedback": feedback,
            },
        )


def _format_feedback(evaluations: list[dict]) -> str:
    parts = []
    for ev in evaluations:
        judge = ev.get("judge_type", "Unknown")
        score = ev.get("score", 0)
        weaknesses = "\n  - ".join(ev.get("weaknesses", []))
        recommendations = "\n  - ".join(ev.get("recommendations", []))
        parts.append(
            f"[{judge} — Score {score:.1f}/10]\n"
            f"Weaknesses:\n  - {weaknesses}\n"
            f"Recommendations:\n  - {recommendations}"
        )
    return "\n\n".join(parts) if parts else "No specific feedback available."
