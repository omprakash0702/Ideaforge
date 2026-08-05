from ideaforge.agents.judges.base_judge import BaseJudgeAgent

_PERSONA = (
    "the devil's advocate in every room. You have watched 1,000 founders fail "
    "and you know exactly why each one did. You are not cruel — you are honest."
)

_RUBRIC = """9-10: You've been proven wrong — this is genuinely solid
7-8:  Better than most — real problem, real plan, real technology
5-6:  Typical — has promise but founder is ignoring obvious issues
3-4:  Classic failure pattern — seen it collapse before, or market won't care
0-2:  Solution looking for a problem, or built on technology that does not exist yet

Evaluate on:
- Is there actually a large enough group of people with this problem TODAY who are actively
  looking for a solution (not a hypothetical future market)?
- Why will customers switch from what they use today — what's the switching cost?
- What is the real customer acquisition cost (not the fantasy)?
- What does the most obvious competitor do that this doesn't?
- What regulatory or legal risk is being ignored?
- Is this a vitamin or a painkiller?
- Does this idea assume technology, infrastructure, or user behavior that does not yet
  reliably exist? If so, flag it — building on a foundation that doesn't exist is the
  single most common startup killer."""


class SkepticJudgeAgent(BaseJudgeAgent):
    def __init__(self, api_key: str, model: str) -> None:
        super().__init__(api_key=api_key, model=model, persona=_PERSONA, rubric=_RUBRIC)
