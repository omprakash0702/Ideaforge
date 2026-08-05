import structlog
from langgraph.graph import END, START, StateGraph

from ideaforge.workflow.deps import WorkflowDeps
from ideaforge.workflow.nodes import (
    make_evolve_node,
    make_generate_node,
    make_judge_node,
    make_rag_fetch_node,
    make_report_node,
    make_tournament_node,
)
from ideaforge.workflow.state import IdeaForgeState

logger = structlog.get_logger(__name__)

_MAX_RETRIES = 2
_RETRY_SCORE_THRESHOLD = 6.0


def _route_after_judge(state: IdeaForgeState) -> str:
    """Return 'generate' to retry if every idea scores below threshold, else 'evolve'.

    Retries are capped at _MAX_RETRIES to prevent infinite loops.
    On retry the generate node appends new ideas so the judge evaluates
    fresh candidates only; the tournament then picks the best from all runs.
    """
    retry_count = state.get("retry_count", 0)
    if retry_count >= _MAX_RETRIES:
        return "evolve"

    evaluations = state.get("evaluations", [])
    if not evaluations:
        return "evolve"

    idea_scores: dict[str, list[float]] = {}
    for ev in evaluations:
        idea_scores.setdefault(ev["idea_id"], []).append(ev["score"])

    if not idea_scores:
        return "evolve"

    max_avg = max(
        sum(scores) / len(scores) for scores in idea_scores.values()
    )

    if max_avg < _RETRY_SCORE_THRESHOLD:
        logger.info(
            "workflow.retry",
            max_score=round(max_avg, 2),
            retry_count=retry_count,
            threshold=_RETRY_SCORE_THRESHOLD,
        )
        return "generate"

    return "evolve"


def build_workflow(deps: WorkflowDeps):
    """Compile the IdeaForge LangGraph workflow with real agent nodes.

    Topology:
        rag_fetch → generate → judge ──(score ≥ 6.0 or retry limit)──▶ evolve → tournament → report
                                  ▲──────(score < 6.0, retry ≤ 2)──────┘

    Conditional retry: if no idea scores ≥ 6.0 after judging, the workflow
    loops back to generate with a stronger prompt and appends fresh ideas
    before re-judging only the new candidates.
    """
    builder = StateGraph(IdeaForgeState)

    builder.add_node("rag_fetch", make_rag_fetch_node(deps))
    builder.add_node("generate", make_generate_node(deps))
    builder.add_node("judge", make_judge_node(deps))
    builder.add_node("evolve", make_evolve_node(deps))
    builder.add_node("tournament", make_tournament_node(deps))
    builder.add_node("report", make_report_node(deps))

    builder.add_edge(START, "rag_fetch")
    builder.add_edge("rag_fetch", "generate")
    builder.add_edge("generate", "judge")

    builder.add_conditional_edges(
        "judge",
        _route_after_judge,
        {"generate": "generate", "evolve": "evolve"},
    )

    builder.add_edge("evolve", "tournament")
    builder.add_edge("tournament", "report")
    builder.add_edge("report", END)

    return builder.compile()
