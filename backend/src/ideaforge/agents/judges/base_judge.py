from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from ideaforge.agents.base import BaseAgent
from ideaforge.agents.schemas import JudgmentSchema

_SYSTEM = """You are {persona}

Your scoring rubric (0-10):
{rubric}

Evaluate the idea against your specific criteria. Be direct, specific, and harsh if warranted.
Generic praise or criticism is useless — cite concrete details from the idea."""

_HUMAN = """Evaluate this startup idea:

Title: {title}
Problem: {problem}
Solution: {solution}
Target Audience: {target_audience}
Business Model: {business_model}
Tech Stack: {tech_stack}
Key Features: {key_features}

Provide your score, specific strengths, specific weaknesses, and concrete recommendations."""

_PROMPT = ChatPromptTemplate.from_messages([("system", _SYSTEM), ("human", _HUMAN)])


class BaseJudgeAgent(BaseAgent):
    _invoke_timeout = 120.0

    def __init__(
        self,
        api_key: str,
        model: str,
        persona: str,
        rubric: str,
    ) -> None:
        _llm = ChatOpenAI(api_key=api_key, model=model, temperature=0, timeout=120)
        self._chain = _PROMPT | _llm.with_structured_output(JudgmentSchema)
        self._persona = persona
        self._rubric = rubric

    async def evaluate(self, idea: dict) -> JudgmentSchema:
        return await self._invoke_with_retry(
            self._chain,
            {
                "persona": self._persona,
                "rubric": self._rubric,
                "title": idea.get("title", ""),
                "problem": idea.get("problem", ""),
                "solution": idea.get("solution", ""),
                "target_audience": idea.get("target_audience", ""),
                "business_model": idea.get("business_model", ""),
                "tech_stack": idea.get("tech_stack", ""),
                "key_features": ", ".join(idea.get("key_features") or []),
            },
        )
