from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from ideaforge.agents.base import BaseAgent
from ideaforge.agents.schemas import ReportSchema

_SYSTEM = """You are a blunt startup critic writing a 2-minute read summary of a winning idea.

FORBIDDEN — do not write any of these:
- Financial projections or revenue numbers
- 90-day or any-day roadmaps
- Team structure or hiring plans
- Go-to-market strategies
- Competitive landscape analysis
- Generic startup advice ("leverage social media", "focus on UX")
- Made-up statistics

REQUIRED — write only what you actually know from the idea and judge feedback:

## What It Is
2–3 sentences. The real problem it solves, the actual solution, who pays and how.
Be concrete — use the specific product/feature details given, not vague descriptions.

## Why It Beat the Others
3 bullet points. Specific reasons this idea scored higher — from the judge evaluations,
not generic praise. Quote or paraphrase what judges actually said.

## What the Judges Flagged
The real concerns raised. Investor, engineer, and skeptic each see different risks —
summarise what each actually said. No softening. If the skeptic said it's doomed, say so.

## Biggest Risk Right Now
One paragraph. The single most dangerous assumption this idea is making.
If it's wrong, the idea fails. Name it clearly.

## First Real Move
One sentence. The single most important thing to validate or build first.
Not a strategy — a specific action."""

_HUMAN = """Problem Statement:
{problem}

Winning Idea:
Title: {title}
Problem: {idea_problem}
Solution: {solution}
Target Audience: {target_audience}
Business Model: {business_model}
Tech Stack: {tech_stack}
Key Features: {key_features}

Judge Evaluations:
{evaluations_text}

Write the summary. Use only information above — no invented details."""

_PROMPT = ChatPromptTemplate.from_messages([("system", _SYSTEM), ("human", _HUMAN)])


class ReportAgent(BaseAgent):
    def __init__(self, api_key: str, model: str) -> None:
        _llm = ChatOpenAI(api_key=api_key, model=model, temperature=0.2, timeout=180)
        self._chain = _PROMPT | _llm.with_structured_output(ReportSchema)

    async def generate(
        self, problem: str, winning_idea: dict, evaluations: list[dict]
    ) -> ReportSchema:
        return await self._invoke_with_retry(
            self._chain,
            {
                "problem": problem,
                "title": winning_idea.get("title", ""),
                "idea_problem": winning_idea.get("problem", ""),
                "solution": winning_idea.get("solution", ""),
                "target_audience": winning_idea.get("target_audience", ""),
                "business_model": winning_idea.get("business_model", ""),
                "tech_stack": winning_idea.get("tech_stack", ""),
                "key_features": ", ".join(winning_idea.get("key_features") or []),
                "evaluations_text": _format_evaluations(evaluations),
            },
        )


def _format_evaluations(evaluations: list[dict]) -> str:
    parts = []
    for ev in evaluations:
        judge = ev.get("judge_type", "Unknown")
        score = ev.get("score", 0)
        strengths = "; ".join(ev.get("strengths", []))
        weaknesses = "; ".join(ev.get("weaknesses", []))
        parts.append(f"[{judge} — {score:.1f}/10] Strengths: {strengths} | Concerns: {weaknesses}")
    return "\n".join(parts) if parts else "No evaluations available."
