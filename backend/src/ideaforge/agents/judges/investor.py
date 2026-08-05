from ideaforge.agents.judges.base_judge import BaseJudgeAgent

_PERSONA = (
    "a hard-nosed Series A investor who has seen 5,000 pitches and funded 12 companies. "
    "You care about one thing: returns."
)

_RUBRIC = """9-10: Exceptional — would write a check today
7-8:  Strong — want a second meeting
5-6:  Interesting — but concerns outweigh excitement
3-4:  Weak — fundamental market or model issues
0-2:  Pass — would not invest under any circumstances

Evaluate on: market size (TAM/SAM/SOM), revenue model clarity, competitive moat,
customer acquisition realism, exit potential (who buys this in 5-7 years?), and
team-market fit indicators."""


class InvestorJudgeAgent(BaseJudgeAgent):
    def __init__(self, api_key: str, model: str) -> None:
        super().__init__(api_key=api_key, model=model, persona=_PERSONA, rubric=_RUBRIC)
