"""LangGraph node implementations.

Each node function is created via a factory that closes over WorkflowDeps,
so the compiled graph carries no global state.

DB writes use AsyncSessionLocal directly — nodes run outside FastAPI's
request lifecycle (as background tasks) and manage their own sessions.

Neo4j writes happen in evolve_node (EVOLVED_INTO relationships) and
tournament_node (tournament_rank / is_winner properties on Idea nodes).
Both fail open — a Neo4j outage does not abort the workflow.
"""

import asyncio
import uuid

import structlog

from ideaforge.agents.schemas import EvolutionSchema
from ideaforge.api.schemas.evaluation import EvaluationCreate
from ideaforge.api.schemas.idea import IdeaCreate, IdeaUpdate
from ideaforge.api.schemas.report import ReportCreate
from ideaforge.core.exceptions import WorkflowError
from ideaforge.domain.enums import GeneratorType, JudgeType, ProjectStatus
from ideaforge.infrastructure.database.neo4j import get_neo4j_driver
from ideaforge.infrastructure.database.postgres import AsyncSessionLocal
from ideaforge.infrastructure.repositories.evaluation_repository import SQLEvaluationRepository
from ideaforge.infrastructure.repositories.idea_repository import SQLIdeaRepository
from ideaforge.infrastructure.repositories.project_repository import SQLProjectRepository
from ideaforge.infrastructure.repositories.report_repository import SQLReportRepository
from ideaforge.workflow.deps import WorkflowDeps
from ideaforge.workflow.state import IdeaForgeState

logger = structlog.get_logger(__name__)

_GENERATOR_TYPES = [GeneratorType.CREATIVE, GeneratorType.MARKET, GeneratorType.BUILDER, GeneratorType.ANALYST]
_JUDGE_TYPES = [JudgeType.INVESTOR, JudgeType.ENGINEER, JudgeType.SKEPTIC]


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _set_status(project_id: uuid.UUID, status: ProjectStatus) -> None:
    async with AsyncSessionLocal() as session:
        await SQLProjectRepository(session).update_status(project_id, status)
        await session.commit()


async def _web_search(query: str, max_results: int = 4) -> str:
    """Live market research via DuckDuckGo. Fails open — returns '' on any error."""
    from duckduckgo_search import DDGS

    def _sync() -> str:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return "\n".join(
            f"• {r['title']}: {r['body'][:250]}" for r in results if r.get("body")
        )

    try:
        return await asyncio.wait_for(asyncio.to_thread(_sync), timeout=15.0)
    except (asyncio.TimeoutError, Exception) as exc:
        logger.warning("web_search.failed", error=str(exc))
        return ""


# ── Node factories ────────────────────────────────────────────────────────────

def make_rag_fetch_node(deps: WorkflowDeps):
    async def node(state: IdeaForgeState) -> dict:
        problem = state["problem_statement"]
        project_id = state["project_id"]
        try:
            ctx = await deps.rag.get_context(project_id, problem)
            logger.info("rag.fetched", project_id=project_id, chunks=len(ctx.chunks))
            return {"rag_context": ctx.context_text}
        except Exception as exc:
            logger.warning("rag.fetch_failed", project_id=project_id, error=str(exc))
            return {"rag_context": ""}

    return node


def make_generate_node(deps: WorkflowDeps):
    async def node(state: IdeaForgeState) -> dict:
        project_id = uuid.UUID(state["project_id"])
        problem = state["problem_statement"]
        rag_ctx = state.get("rag_context") or ""
        retry_count = state.get("retry_count", 0)

        # On retries push generators to think more boldly
        effective_problem = problem
        if retry_count > 0:
            effective_problem = (
                f"{problem}\n\n"
                f"[Retry {retry_count}: previous ideas scored below 6.0 — "
                "generate bolder, more differentiated concepts with a clear unfair advantage.]"
            )

        await _set_status(project_id, ProjectStatus.GENERATING)
        logger.info("generate.start", project_id=str(project_id), retry=retry_count)

        # Web search for live market intelligence (runs in parallel with nothing to block it)
        search_query = f"startup market opportunity {problem[:120]}"
        web_ctx = await _web_search(search_query)
        if web_ctx:
            logger.info("web_search.done", project_id=str(project_id), chars=len(web_ctx))

        # Run all 4 generators concurrently (Gemini: creative/market/builder + OpenAI: analyst)
        results = await asyncio.gather(
            deps.creative.generate(effective_problem, rag_ctx, web_ctx),
            deps.market.generate(effective_problem, rag_ctx, web_ctx),
            deps.builder.generate(effective_problem, rag_ctx, web_ctx),
            deps.analyst.generate(effective_problem, rag_ctx, web_ctx),
            return_exceptions=True,
        )

        ideas_to_save: list[tuple[GeneratorType, object]] = []
        for gen_type, result in zip(_GENERATOR_TYPES, results):
            if isinstance(result, Exception):
                logger.error("generator.failed", gen_type=gen_type.value, error=str(result))
            else:
                for idea_schema in result.ideas:
                    idea_text = (
                        f"{idea_schema.title}. {idea_schema.problem}. "
                        f"{idea_schema.solution}. {idea_schema.business_model}"
                    )
                    gr = deps.guard.check_sync(idea_text)
                    if not gr.safe:
                        logger.warning(
                            "guardrail.generated_idea_blocked",
                            project_id=str(project_id),
                            title=idea_schema.title[:60],
                            category=gr.category,
                            reason=gr.reason,
                        )
                    else:
                        ideas_to_save.append((gen_type, idea_schema))

        if not ideas_to_save:
            raise WorkflowError("All generator agents failed — cannot continue.")

        # Persist to DB and build state list
        new_ideas: list[dict] = []
        async with AsyncSessionLocal() as session:
            repo = SQLIdeaRepository(session)
            for gen_type, schema in ideas_to_save:
                idea = await repo.create(
                    IdeaCreate(
                        project_id=project_id,
                        generator_type=gen_type,
                        **schema.model_dump(),
                    )
                )
                new_ideas.append(_idea_to_dict(idea))
            await session.commit()

        # ── Neo4j: batch-write all Idea nodes via execute_write ──────────────
        try:
            driver = await get_neo4j_driver()
            batch = [
                {
                    "id": idea["id"],
                    "project_id": str(project_id),
                    "title": idea["title"],
                    "problem": idea.get("problem", ""),
                    "solution": idea.get("solution", ""),
                    "target_audience": idea.get("target_audience", ""),
                    "business_model": idea.get("business_model", ""),
                    "tech_stack": idea.get("tech_stack", ""),
                    "key_features": idea.get("key_features") or [],
                    "competitors": idea.get("competitors") or [],
                    "generator_type": (
                        idea["generator_type"].value
                        if hasattr(idea.get("generator_type"), "value")
                        else str(idea.get("generator_type") or "")
                    ),
                }
                for idea in new_ideas
            ]
            async with driver.session() as neo4j_session:
                async def _write_ideas(tx):
                    r = await tx.run(
                        """
                        UNWIND $batch AS i
                        MERGE (n:Idea {id: i.id, project_id: i.project_id})
                        SET n.title           = i.title,
                            n.problem         = i.problem,
                            n.solution        = i.solution,
                            n.target_audience = i.target_audience,
                            n.business_model  = i.business_model,
                            n.tech_stack      = i.tech_stack,
                            n.key_features    = i.key_features,
                            n.competitors     = i.competitors,
                            n.version         = 1,
                            n.generator_type  = i.generator_type
                        """,
                        batch=batch,
                    )
                    await r.consume()
                await neo4j_session.execute_write(_write_ideas)
            logger.info("neo4j.ideas_written", project_id=str(project_id), count=len(new_ideas))
        except Exception as exc:
            logger.warning("neo4j.ideas_failed", project_id=str(project_id), error=str(exc))

        # Accumulate ideas across retries so the tournament sees all candidates
        existing_ideas = state.get("generated_ideas") or []
        all_ideas = existing_ideas + new_ideas

        logger.info(
            "generate.done",
            project_id=str(project_id),
            new=len(new_ideas),
            total=len(all_ideas),
            retry=retry_count,
        )
        return {
            "generated_ideas": all_ideas,
            "retry_count": retry_count + 1,
            "current_stage": ProjectStatus.JUDGING.value,
        }

    return node


def make_judge_node(deps: WorkflowDeps):
    async def node(state: IdeaForgeState) -> dict:
        project_id = uuid.UUID(state["project_id"])
        all_ideas = state.get("generated_ideas", [])
        existing_evals = state.get("evaluations") or []

        await _set_status(project_id, ProjectStatus.JUDGING)

        # On retry: only judge ideas that haven't been evaluated yet
        evaluated_ids = {ev["idea_id"] for ev in existing_evals}
        ideas_to_judge = [i for i in all_ideas if i["id"] not in evaluated_ids]

        if not ideas_to_judge:
            logger.info("judge.skip", reason="all ideas already evaluated")
            return {"evaluations": existing_evals}

        # Judge all new ideas concurrently (3 judges × N ideas)
        per_idea_results = await asyncio.gather(
            *[_judge_one_idea(idea, deps) for idea in ideas_to_judge],
            return_exceptions=True,
        )
        new_evals: list[dict] = []
        for result in per_idea_results:
            if isinstance(result, Exception):
                logger.error("judge_idea.failed", error=str(result))
            else:
                new_evals.extend(result)

        # Persist new evaluations
        async with AsyncSessionLocal() as session:
            repo = SQLEvaluationRepository(session)
            for ev in new_evals:
                await repo.create(
                    EvaluationCreate(
                        idea_id=uuid.UUID(ev["idea_id"]),
                        judge_type=ev["judge_type"],
                        score=ev["score"],
                        strengths=ev["strengths"],
                        weaknesses=ev["weaknesses"],
                        recommendations=ev["recommendations"],
                    )
                )
            await session.commit()

        # ── Neo4j: batch-write Judge nodes + EVALUATED relationships ─────────
        if new_evals:
            try:
                driver = await get_neo4j_driver()
                batch = [
                    {
                        "judge_id": f"{ev['judge_type']}_{project_id}",
                        "project_id": str(project_id),
                        "judge_type": ev["judge_type"],
                        "idea_id": ev["idea_id"],
                        "score": ev["score"],
                        "strengths": ev["strengths"],
                        "weaknesses": ev["weaknesses"],
                        "recommendations": ev["recommendations"],
                    }
                    for ev in new_evals
                ]
                async with driver.session() as neo4j_session:
                    async def _write_evals(tx):
                        r = await tx.run(
                            """
                            UNWIND $batch AS ev
                            MERGE (j:Judge {id: ev.judge_id, project_id: ev.project_id})
                            SET j.type = ev.judge_type
                            WITH j, ev
                            MERGE (i:Idea {id: ev.idea_id, project_id: ev.project_id})
                            MERGE (j)-[r:EVALUATED]->(i)
                            SET r.score           = ev.score,
                                r.strengths       = ev.strengths,
                                r.weaknesses      = ev.weaknesses,
                                r.recommendations = ev.recommendations
                            """,
                            batch=batch,
                        )
                        await r.consume()
                    await neo4j_session.execute_write(_write_evals)
                logger.info("neo4j.evaluations_written", project_id=str(project_id), count=len(new_evals))
            except Exception as exc:
                logger.warning("neo4j.evaluations_failed", project_id=str(project_id), error=str(exc))

        all_evals = existing_evals + new_evals
        if not all_evals:
            raise WorkflowError(
                "No ideas were successfully evaluated — all judge agents failed. "
                "Cannot proceed to tournament without real scores."
            )
        logger.info(
            "judge.done",
            project_id=str(project_id),
            new_evaluations=len(new_evals),
            total_evaluations=len(all_evals),
        )
        return {"evaluations": all_evals, "current_stage": ProjectStatus.EVOLVING.value}

    return node


def make_evolve_node(deps: WorkflowDeps):
    async def node(state: IdeaForgeState) -> dict:
        project_id = uuid.UUID(state["project_id"])
        ideas = list(state.get("generated_ideas", []))
        evaluations = state.get("evaluations", [])

        await _set_status(project_id, ProjectStatus.EVOLVING)

        # Attach aggregate scores to each idea
        scores_map: dict[str, list[float]] = {}
        for ev in evaluations:
            scores_map.setdefault(ev["idea_id"], []).append(ev["score"])

        for idea in ideas:
            ev_scores = scores_map.get(idea["id"], [5.0])
            idea["score"] = round(sum(ev_scores) / len(ev_scores), 2)

        # Evolve up to 5 of the lower-scoring ideas (at minimum 2, to ensure variety)
        sorted_ideas = sorted(ideas, key=lambda x: x.get("score", 5.0))
        n_below_threshold = sum(1 for i in sorted_ideas if i.get("score", 5.0) < 7.5)
        to_evolve = sorted_ideas[:max(2, min(5, n_below_threshold))]

        evolution_results = await asyncio.gather(
            *[_evolve_one_idea(idea, evaluations, deps) for idea in to_evolve],
            return_exceptions=True,
        )

        evolved_ideas: list[dict] = []
        async with AsyncSessionLocal() as session:
            repo = SQLIdeaRepository(session)
            for original, result in zip(to_evolve, evolution_results):
                if isinstance(result, Exception):
                    logger.warning(
                        "evolution.skipped",
                        idea=original.get("title"),
                        error=str(result),
                    )
                    continue
                evolved_schema: EvolutionSchema = result
                evo_text = (
                    f"{evolved_schema.title}. {evolved_schema.problem}. "
                    f"{evolved_schema.solution}. {evolved_schema.business_model}"
                )
                gr = deps.guard.check_sync(evo_text)
                if not gr.safe:
                    logger.warning(
                        "guardrail.evolved_idea_blocked",
                        project_id=str(project_id),
                        title=evolved_schema.title[:60],
                        category=gr.category,
                        reason=gr.reason,
                    )
                    continue
                idea_db = await repo.create(
                    IdeaCreate(
                        project_id=project_id,
                        parent_idea_id=uuid.UUID(original["id"]),
                        version=2,
                        generator_type=original.get("generator_type") or GeneratorType.CREATIVE,
                        title=evolved_schema.title,
                        problem=evolved_schema.problem,
                        solution=evolved_schema.solution,
                        target_audience=evolved_schema.target_audience,
                        business_model=evolved_schema.business_model,
                        tech_stack=evolved_schema.tech_stack,
                        key_features=evolved_schema.key_features,
                    )
                )
                score_before = original.get("score", 5.0)
                score_after = min(score_before + 1.5, 10.0)
                evolved_dict = _idea_to_dict(idea_db)
                evolved_dict.update({
                    "is_evolved": True,
                    "parent_id": original["id"],
                    "score": score_after,
                    "evolution_rationale": evolved_schema.evolution_rationale,
                    "score_before": score_before,
                    "competitors": original.get("competitors") or [],
                })
                evolved_ideas.append(evolved_dict)
            await session.commit()

        # ── Neo4j: batch-write EVOLVED_INTO relationships ────────────────────
        if evolved_ideas:
            try:
                driver = await get_neo4j_driver()
                batch = []
                for ev_dict in evolved_ideas:
                    score_b = ev_dict.get("score_before", 5.0)
                    score_a = ev_dict.get("score", score_b)
                    gt = ev_dict.get("generator_type")
                    batch.append({
                        "parent_id": ev_dict["parent_id"],
                        "child_id": ev_dict["id"],
                        "project_id": str(project_id),
                        "title": ev_dict["title"],
                        "problem": ev_dict.get("problem", ""),
                        "solution": ev_dict.get("solution", ""),
                        "target_audience": ev_dict.get("target_audience", ""),
                        "business_model": ev_dict.get("business_model", ""),
                        "tech_stack": ev_dict.get("tech_stack", ""),
                        "key_features": ev_dict.get("key_features") or [],
                        "competitors": ev_dict.get("competitors") or [],
                        "generator_type": gt.value if hasattr(gt, "value") else str(gt or ""),
                        "rationale": ev_dict.get("evolution_rationale", ""),
                        "score_before": score_b,
                        "score_after": score_a,
                        "score_delta": round(score_a - score_b, 2),
                    })
                async with driver.session() as neo4j_session:
                    async def _write_evo(tx):
                        r = await tx.run(
                            """
                            UNWIND $batch AS ev
                            MERGE (p:Idea {id: ev.parent_id, project_id: ev.project_id})
                            MERGE (c:Idea {id: ev.child_id, project_id: ev.project_id})
                            SET c.title           = ev.title,
                                c.problem         = ev.problem,
                                c.solution        = ev.solution,
                                c.target_audience = ev.target_audience,
                                c.business_model  = ev.business_model,
                                c.tech_stack      = ev.tech_stack,
                                c.key_features    = ev.key_features,
                                c.competitors     = ev.competitors,
                                c.version         = 2,
                                c.generator_type  = ev.generator_type
                            WITH p, c, ev
                            MERGE (p)-[r:EVOLVED_INTO]->(c)
                            SET r.evolution_rationale = ev.rationale,
                                r.score_before        = ev.score_before,
                                r.score_after         = ev.score_after,
                                r.score_delta         = ev.score_delta
                            """,
                            batch=batch,
                        )
                        await r.consume()
                    await neo4j_session.execute_write(_write_evo)
                logger.info("neo4j.evolve_written", project_id=str(project_id), count=len(evolved_ideas))
            except Exception as exc:
                logger.warning("neo4j.evolve_failed", project_id=str(project_id), error=str(exc))

        # Persist computed scores to PostgreSQL so /ideas endpoint has real data
        async with AsyncSessionLocal() as session:
            score_repo = SQLIdeaRepository(session)
            for idea in ideas:
                s = idea.get("score")
                if s is not None:
                    try:
                        await score_repo.update(uuid.UUID(idea["id"]), IdeaUpdate(score=round(float(s), 2)))
                    except Exception as exc:
                        logger.warning("score_save.v1.failed", idea_id=idea["id"], error=str(exc))
            for ev_dict in evolved_ideas:
                s = ev_dict.get("score")
                if s is not None:
                    try:
                        await score_repo.update(uuid.UUID(ev_dict["id"]), IdeaUpdate(score=round(float(s), 2)))
                    except Exception as exc:
                        logger.warning("score_save.v2.failed", idea_id=ev_dict["id"], error=str(exc))
            await session.commit()
        logger.info("scores.saved_to_db", project_id=str(project_id))

        all_ideas = ideas + evolved_ideas
        logger.info(
            "evolve.done",
            project_id=str(project_id),
            evolved=len(evolved_ideas),
            total=len(all_ideas),
        )
        return {
            "generated_ideas": all_ideas,
            "evolved_ideas": evolved_ideas,
            "current_stage": ProjectStatus.TOURNAMENT.value,
        }

    return node


def make_tournament_node(deps: WorkflowDeps):
    async def node(state: IdeaForgeState) -> dict:
        project_id = uuid.UUID(state["project_id"])
        ideas = state.get("generated_ideas", [])
        evaluations = state.get("evaluations", [])

        await _set_status(project_id, ProjectStatus.TOURNAMENT)

        if not ideas:
            raise WorkflowError("Tournament received no ideas — cannot determine a winner.")

        result = deps.tournament.run(ideas, evaluations)
        winner = result.winner

        # ── PostgreSQL: mark winner + save tournament aggregate scores ─────────
        async with AsyncSessionLocal() as session:
            repo = SQLIdeaRepository(session)
            await repo.mark_winner(uuid.UUID(winner["id"]))
            for ranked_idea in result.ranked_ideas:
                agg = ranked_idea.get("aggregate_score")
                if agg is not None:
                    try:
                        await repo.update(
                            uuid.UUID(ranked_idea["id"]),
                            IdeaUpdate(score=round(float(agg), 2)),
                        )
                    except Exception as exc:
                        logger.warning("tournament_score.save_failed", idea_id=ranked_idea["id"], error=str(exc))
            await session.commit()

        # ── Neo4j: batch-write tournament ranks + RANKED_ABOVE chain ─────────
        try:
            driver = await get_neo4j_driver()
            ranked = result.ranked_ideas
            rank_batch = [
                {
                    "idea_id": ri["id"],
                    "project_id": str(project_id),
                    "title": ri.get("title", ""),
                    "rank": rank,
                    "score": ri.get("aggregate_score", 5.0),
                    "is_winner": ri["id"] == winner["id"],
                }
                for rank, ri in enumerate(ranked, start=1)
            ]
            pair_batch = [
                {
                    "a_id": ranked[i]["id"],
                    "b_id": ranked[i + 1]["id"],
                    "pid": str(project_id),
                    "diff": round(
                        ranked[i].get("aggregate_score", 0)
                        - ranked[i + 1].get("aggregate_score", 0),
                        2,
                    ),
                }
                for i in range(len(ranked) - 1)
            ]
            async with driver.session() as neo4j_session:
                async def _write_tournament(tx):
                    r1 = await tx.run(
                        """
                        UNWIND $batch AS i
                        MERGE (n:Idea {id: i.idea_id, project_id: i.project_id})
                        SET n.title           = i.title,
                            n.tournament_rank = i.rank,
                            n.aggregate_score = i.score,
                            n.is_winner       = i.is_winner
                        """,
                        batch=rank_batch,
                    )
                    await r1.consume()
                    if pair_batch:
                        r2 = await tx.run(
                            """
                            UNWIND $pairs AS p
                            MATCH (a:Idea {id: p.a_id, project_id: p.pid})
                            MATCH (b:Idea {id: p.b_id, project_id: p.pid})
                            MERGE (a)-[r:RANKED_ABOVE]->(b)
                            SET r.score_diff = p.diff
                            """,
                            pairs=pair_batch,
                        )
                        await r2.consume()
                await neo4j_session.execute_write(_write_tournament)
            logger.info(
                "neo4j.tournament_written",
                project_id=str(project_id),
                nodes=len(ranked),
            )
        except Exception as exc:
            logger.warning("neo4j.tournament_failed", project_id=str(project_id), error=str(exc))

        logger.info(
            "tournament.done",
            project_id=str(project_id),
            winner=winner.get("title"),
            score=winner.get("aggregate_score"),
        )
        return {
            "tournament_results": result.ranked_ideas,
            "winning_idea": winner,
            "current_stage": ProjectStatus.REPORTING.value,
        }

    return node


def make_report_node(deps: WorkflowDeps):
    async def node(state: IdeaForgeState) -> dict:
        project_id = uuid.UUID(state["project_id"])
        winner = state.get("winning_idea", {})
        all_evals = state.get("evaluations", [])
        problem = state["problem_statement"]

        if not winner.get("id"):
            raise WorkflowError("No winning idea found — cannot generate report.")

        await _set_status(project_id, ProjectStatus.REPORTING)

        winner_evals = [e for e in all_evals if e.get("idea_id") == winner.get("id")]
        try:
            report_schema = await deps.report_agent.generate(
                problem=problem,
                winning_idea=winner,
                evaluations=winner_evals,
            )
        except Exception as exc:
            raise WorkflowError(f"Report generation failed: {exc}") from exc

        async with AsyncSessionLocal() as session:
            report_repo = SQLReportRepository(session)
            await report_repo.create(
                ReportCreate(
                    project_id=project_id,
                    winner_idea_id=uuid.UUID(winner["id"]) if winner.get("id") else None,
                    markdown_report=report_schema.markdown_report,
                )
            )
            project_repo = SQLProjectRepository(session)
            await project_repo.update_status(project_id, ProjectStatus.COMPLETED)
            await session.commit()

        logger.info("report.done", project_id=str(project_id))
        return {
            "final_report": report_schema.markdown_report,
            "current_stage": ProjectStatus.COMPLETED.value,
        }

    return node


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _judge_one_idea(idea: dict, deps: WorkflowDeps) -> list[dict]:
    """Run all 3 judges on a single idea concurrently.

    Raises WorkflowError if every judge fails so the outer gather can track
    per-idea failures without injecting fabricated scores.
    """
    results = await asyncio.gather(
        deps.investor.evaluate(idea),
        deps.engineer.evaluate(idea),
        deps.skeptic.evaluate(idea),
        return_exceptions=True,
    )
    evals: list[dict] = []
    for judge_type, result in zip(_JUDGE_TYPES, results):
        if isinstance(result, Exception):
            logger.warning(
                "judge.failed",
                judge=judge_type.value,
                idea=idea.get("title"),
                error=str(result),
            )
        else:
            evals.append({
                "idea_id": idea["id"],
                "judge_type": judge_type.value,
                "score": result.score,
                "strengths": result.strengths,
                "weaknesses": result.weaknesses,
                "recommendations": result.recommendations,
            })
    if not evals:
        raise WorkflowError(
            f"All 3 judges failed for idea '{idea.get('title')}' — no real scores available"
        )
    return evals


async def _evolve_one_idea(
    idea: dict, evaluations: list[dict], deps: WorkflowDeps
) -> EvolutionSchema:
    idea_evals = [e for e in evaluations if e.get("idea_id") == idea["id"]]
    return await deps.evolution.evolve(idea, idea_evals)


def _idea_to_dict(idea) -> dict:
    return {
        "id": str(idea.id),
        "title": idea.title,
        "problem": idea.problem,
        "solution": idea.solution,
        "target_audience": idea.target_audience,
        "business_model": idea.business_model,
        "tech_stack": idea.tech_stack,
        "key_features": idea.key_features or [],
        "competitors": idea.competitors or [],
        "generator_type": idea.generator_type,
        "score": idea.score,
        "is_evolved": False,
        "parent_id": str(idea.parent_idea_id) if idea.parent_idea_id else None,
    }
