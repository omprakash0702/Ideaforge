from typing import NotRequired, Required, TypedDict


class IdeaForgeState(TypedDict, total=False):
    """Shared state passed between every node in the LangGraph workflow.

    total=False — all keys are optional by default; nodes add only what they
    produce and downstream nodes use .get() for absent keys.

    project_id and problem_statement are Required so the type checker enforces
    them at graph invocation time — every other key is populated progressively.
    """

    # ── Required at invocation ────────────────────────────────────────────────
    project_id: Required[str]
    problem_statement: Required[str]

    # ── RAG — retrieved document context (injected before generation) ─────────
    rag_context: NotRequired[str]  # joined chunks from RAGPipeline.get_context()

    # ── Stage outputs — populated as the workflow progresses ──────────────────
    generated_ideas: NotRequired[list[dict]]    # Generator node output (6 ideas)
    evaluations: NotRequired[list[dict]]        # Judge node output (3 judges × N ideas)
    evolved_ideas: NotRequired[list[dict]]      # Evolution node output
    tournament_results: NotRequired[list[dict]] # Tournament node output
    winning_idea: NotRequired[dict]             # Single winner from tournament
    final_report: NotRequired[str]              # Markdown report from Report node

    # ── Workflow control ──────────────────────────────────────────────────────
    current_stage: NotRequired[str]   # mirrors ProjectStatus enum values
    errors: NotRequired[list[str]]    # accumulated non-fatal error messages
    retry_count: NotRequired[int]     # how many generate→judge loops have run (max 2)
