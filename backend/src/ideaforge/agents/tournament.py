"""Tournament agent — pure Python ranking, no LLM calls.

Aggregates judge scores per idea, ranks all ideas (including evolved variants),
and returns the winner plus the full ranked bracket.
"""

from dataclasses import dataclass


@dataclass
class TournamentResult:
    winner: dict
    ranked_ideas: list[dict]  # sorted highest → lowest aggregate score


class TournamentAgent:
    """Stateless scoring and ranking logic."""

    def run(self, ideas: list[dict], evaluations: list[dict]) -> TournamentResult:
        """Rank all ideas by aggregate judge score and return the winner.

        Evolved ideas inherit their parent's evaluations if they have none of their own,
        plus a +1.0 evolution bonus that represents the improvement from feedback.
        """
        # Build score lookup: idea_id → list of individual judge scores
        scores_by_idea: dict[str, list[float]] = {}
        for ev in evaluations:
            idea_id = ev.get("idea_id", "")
            scores_by_idea.setdefault(idea_id, []).append(ev.get("score", 5.0))

        ranked = []
        for idea in ideas:
            idea_id = idea.get("id", "")
            judge_scores = scores_by_idea.get(idea_id, [])

            if judge_scores:
                aggregate = sum(judge_scores) / len(judge_scores)
            elif idea.get("is_evolved") and idea.get("parent_id"):
                # Evolved idea with no direct judgments — inherit parent + bonus
                parent_scores = scores_by_idea.get(idea["parent_id"], [5.0])
                aggregate = sum(parent_scores) / len(parent_scores) + 1.0
            else:
                aggregate = 5.0  # fallback

            aggregate = min(aggregate, 10.0)
            ranked.append({**idea, "aggregate_score": round(aggregate, 2)})

        ranked.sort(key=lambda x: x["aggregate_score"], reverse=True)
        if not ranked:
            raise ValueError("Tournament received no ideas — cannot determine a winner.")
        return TournamentResult(winner=ranked[0], ranked_ideas=ranked)
