import asyncio
import uuid

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException, status

log = structlog.get_logger(__name__)

from ideaforge.api.dependencies import (
    DBSession,
    EvaluationRepo,
    Guard,
    IdeaRepo,
    Neo4jDriver,
    ProjectRepo,
    ReportRepo,
    UserRepo,
    get_workflow_service,
)
from ideaforge.api.schemas.common import StatusResponse
from ideaforge.api.schemas.evaluation import EvaluationCreate, EvaluationResponse
from ideaforge.api.schemas.idea import (
    ConstrainedGenerateRequest,
    EvaluationEdge,
    IdeaCreate,
    IdeaGraphEdge,
    IdeaGraphNode,
    IdeaGraphResponse,
    IdeaResponse,
    IdeaUpdate,
    JudgeNode,
    UserIdeaCreate,
)
from ideaforge.api.schemas.project import ProjectCreate, ProjectResponse
from ideaforge.api.schemas.report import ReportResponse
from ideaforge.application.services.project_service import ProjectService
from ideaforge.application.services.workflow_service import WorkflowService
from ideaforge.core.exceptions import ConflictError, NotFoundError
from ideaforge.domain.enums import JudgeType

router = APIRouter(prefix="/projects", tags=["projects"])


def _svc(
    project_repo: ProjectRepo,
    user_repo: UserRepo,
    idea_repo: IdeaRepo,
    report_repo: ReportRepo,
) -> ProjectService:
    return ProjectService(
        project_repo=project_repo,
        user_repo=user_repo,
        idea_repo=idea_repo,
        report_repo=report_repo,
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    guard: Guard,
    project_repo: ProjectRepo,
    user_repo: UserRepo,
    idea_repo: IdeaRepo,
    report_repo: ReportRepo,
) -> ProjectResponse:
    result = await guard.check(body.problem_statement)
    if not result.safe:
        from ideaforge.guardrails.schemas import ViolationCategory
        if result.category == ViolationCategory.AMBIGUOUS:
            prefix = "Please clarify your idea"
        else:
            prefix = f"Idea not accepted ({result.category.value.replace('_', ' ').title()})"
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{prefix}: {result.reason}",
        )
    try:
        project = await _svc(project_repo, user_repo, idea_repo, report_repo).create(body)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return ProjectResponse.model_validate(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    project_repo: ProjectRepo,
    user_repo: UserRepo,
    idea_repo: IdeaRepo,
    report_repo: ReportRepo,
) -> ProjectResponse:
    try:
        project = await _svc(project_repo, user_repo, idea_repo, report_repo).get(project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return ProjectResponse.model_validate(project)


@router.post(
    "/{project_id}/run",
    response_model=StatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger AI workflow (non-blocking)",
)
async def run_workflow(
    project_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: DBSession,
    project_repo: ProjectRepo,
    user_repo: UserRepo,
    idea_repo: IdeaRepo,
    report_repo: ReportRepo,
) -> StatusResponse:
    """Start the IdeaForge pipeline for a project.

    Returns 202 immediately. Poll `GET /projects/{id}` for status.
    Terminal statuses: **COMPLETED** or **FAILED**.
    """
    svc = _svc(project_repo, user_repo, idea_repo, report_repo)
    try:
        project = await svc.mark_running(project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    # Commit now so the row lock on the project is released before the background
    # task starts. Without this, _set_status in the generate node deadlocks waiting
    # for this session's uncommitted UPDATE to the same project row.
    await db.commit()

    workflow_svc: WorkflowService = get_workflow_service()
    background_tasks.add_task(
        workflow_svc.run,
        project_id=str(project_id),
        problem_statement=project.problem_statement,
    )
    return StatusResponse(
        status=project.status,
        message="Workflow started. Poll GET /projects/{id} for updates.",
    )


@router.get("/{project_id}/ideas", response_model=list[IdeaResponse])
async def list_ideas(
    project_id: uuid.UUID,
    project_repo: ProjectRepo,
    user_repo: UserRepo,
    idea_repo: IdeaRepo,
    report_repo: ReportRepo,
) -> list[IdeaResponse]:
    try:
        ideas = await _svc(project_repo, user_repo, idea_repo, report_repo).get_ideas(project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return [IdeaResponse.model_validate(i) for i in ideas]


@router.get("/{project_id}/evaluations", response_model=list[EvaluationResponse])
async def list_evaluations(
    project_id: uuid.UUID,
    eval_repo: EvaluationRepo,
) -> list[EvaluationResponse]:
    """Return all judge evaluations for every idea in the project (from PostgreSQL)."""
    evals = await eval_repo.list_by_project(project_id)
    return [EvaluationResponse.model_validate(e) for e in evals]


@router.post("/{project_id}/ideas", response_model=IdeaResponse, status_code=status.HTTP_201_CREATED)
async def add_user_idea(
    project_id: uuid.UUID,
    body: UserIdeaCreate,
    db: DBSession,
    idea_repo: IdeaRepo,
    eval_repo: EvaluationRepo,
    neo4j: Neo4jDriver,
) -> IdeaResponse:
    """Submit a custom idea to be judged by the AI council synchronously."""
    from ideaforge.api.dependencies import _get_workflow_deps, _get_content_guard
    from ideaforge.guardrails.schemas import ViolationCategory

    deps = _get_workflow_deps()

    idea_text = (
        f"{body.title}. {body.problem}. {body.solution}. "
        f"Business model: {body.business_model}. Target audience: {body.target_audience}"
    )
    gr = await _get_content_guard().check(idea_text)
    if not gr.safe:
        prefix = (
            "Please clarify your idea"
            if gr.category == ViolationCategory.AMBIGUOUS
            else f"Idea not accepted ({gr.category.value.replace('_', ' ').title()})"
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{prefix}: {gr.reason}",
        )

    idea = await idea_repo.create(IdeaCreate(
        project_id=project_id,
        generator_type=None,
        title=body.title,
        problem=body.problem,
        solution=body.solution,
        target_audience=body.target_audience,
        business_model=body.business_model,
        tech_stack=body.tech_stack,
        key_features=body.key_features,
        competitors=body.competitors,
    ))
    await db.commit()
    await db.refresh(idea)

    idea_dict = {
        "id": str(idea.id),
        "title": idea.title,
        "problem": idea.problem,
        "solution": idea.solution,
        "target_audience": idea.target_audience,
        "business_model": idea.business_model,
        "tech_stack": idea.tech_stack,
        "key_features": idea.key_features or [],
    }

    results = await asyncio.gather(
        deps.investor.evaluate(idea_dict),
        deps.engineer.evaluate(idea_dict),
        deps.skeptic.evaluate(idea_dict),
        return_exceptions=True,
    )

    judges = [JudgeType.INVESTOR, JudgeType.ENGINEER, JudgeType.SKEPTIC]
    scores: list[float] = []
    evals_to_create: list[EvaluationCreate] = []
    for judge_type, result in zip(judges, results):
        if isinstance(result, Exception):
            log.warning("user_idea.judge_failed", judge=judge_type.value, error=str(result))
            continue
        scores.append(result.score)
        evals_to_create.append(EvaluationCreate(
            idea_id=idea.id,
            judge_type=judge_type,
            score=result.score,
            strengths=result.strengths,
            weaknesses=result.weaknesses,
            recommendations=result.recommendations,
        ))

    if evals_to_create:
        await eval_repo.create_bulk(evals_to_create)

    if scores:
        avg_score = round(sum(scores) / len(scores), 2)
        await idea_repo.update(idea.id, IdeaUpdate(score=avg_score))

    await db.commit()
    await db.refresh(idea)

    pid = str(project_id)
    try:
        async with neo4j.session() as neo4j_session:
            batch = [{
                "id": str(idea.id),
                "project_id": pid,
                "title": idea.title,
                "problem": idea.problem,
                "solution": idea.solution,
                "target_audience": idea.target_audience,
                "business_model": idea.business_model,
                "tech_stack": idea.tech_stack,
                "key_features": idea.key_features or [],
                "competitors": idea.competitors or [],
                "generator_type": "USER",
                "aggregate_score": idea.score,
            }]

            async def _write_user_idea(tx):
                r = await tx.run("""
                    UNWIND $batch AS i
                    MERGE (n:Idea {id: i.id, project_id: i.project_id})
                    SET n.title = i.title, n.problem = i.problem,
                        n.solution = i.solution, n.target_audience = i.target_audience,
                        n.business_model = i.business_model, n.tech_stack = i.tech_stack,
                        n.key_features = i.key_features, n.competitors = i.competitors,
                        n.version = 1, n.generator_type = i.generator_type,
                        n.aggregate_score = i.aggregate_score
                """, batch=batch)
                await r.consume()

            await neo4j_session.execute_write(_write_user_idea)
    except Exception as exc:
        log.warning("user_idea.neo4j_write_skipped", project_id=pid, error=str(exc))

    log.info("user_idea.created", project_id=pid, idea_id=str(idea.id), score=idea.score)
    return IdeaResponse.model_validate(idea)


@router.post("/{project_id}/ideas/{idea_id}/evolve", response_model=list[IdeaResponse])
async def evolve_idea_manual(
    project_id: uuid.UUID,
    idea_id: uuid.UUID,
    db: DBSession,
    idea_repo: IdeaRepo,
    eval_repo: EvaluationRepo,
    neo4j: Neo4jDriver,
) -> list[IdeaResponse]:
    """Generate up to 3 evolved variants of an idea, each fully judged by the council."""
    from ideaforge.api.dependencies import _get_workflow_deps

    deps = _get_workflow_deps()

    idea = await idea_repo.get_by_id(idea_id)
    if not idea:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Idea not found")

    existing_evals = await eval_repo.list_by_idea(idea_id)

    idea_dict = {
        "id": str(idea.id),
        "title": idea.title,
        "problem": idea.problem,
        "solution": idea.solution,
        "target_audience": idea.target_audience,
        "business_model": idea.business_model,
        "tech_stack": idea.tech_stack,
        "key_features": idea.key_features or [],
    }
    eval_dicts = [
        {
            "judge_type": ev.judge_type.value if hasattr(ev.judge_type, "value") else str(ev.judge_type),
            "score": ev.score,
            "weaknesses": ev.weaknesses or [],
            "recommendations": ev.recommendations or [],
        }
        for ev in existing_evals
    ]

    # Generate 3 evolved variants concurrently (temperature=0.3 ensures diversity)
    evo_results = await asyncio.gather(
        *[deps.evolution.evolve(idea_dict, eval_dicts) for _ in range(3)],
        return_exceptions=True,
    )

    # Deduplicate by title
    seen_titles: set[str] = set()
    valid_evolutions = []
    for r in evo_results:
        if isinstance(r, Exception):
            log.warning("manual_evolve.evo_failed", idea_id=str(idea_id), error=str(r))
            continue
        key = r.title.strip().lower()
        if key not in seen_titles:
            seen_titles.add(key)
            valid_evolutions.append(r)

    if not valid_evolutions:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="All evolution attempts failed — try again",
        )

    # Guardrail: filter evolved variants that contain problematic content
    from ideaforge.api.dependencies import _get_content_guard
    guard = _get_content_guard()
    clean_evolutions = []
    for evo in valid_evolutions:
        evo_text = f"{evo.title}. {evo.problem}. {evo.solution}. {evo.business_model}"
        gr = guard.check_sync(evo_text)
        if not gr.safe:
            log.warning(
                "guardrail.manual_evo_blocked",
                idea_id=str(idea_id),
                title=evo.title[:60],
                category=gr.category,
            )
        else:
            clean_evolutions.append(evo)

    if not clean_evolutions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="All evolved variants were blocked by content guardrails. The original idea may contain content that cannot be evolved on this platform.",
        )
    valid_evolutions = clean_evolutions

    # Create all evolved ideas in DB
    new_version = min((idea.version or 1) + 1, 4)
    created: list[tuple] = []  # (idea_orm, rationale)
    for evo in valid_evolutions:
        new_idea = await idea_repo.create(IdeaCreate(
            project_id=project_id,
            parent_idea_id=idea_id,
            version=new_version,
            generator_type=idea.generator_type,
            title=evo.title,
            problem=evo.problem,
            solution=evo.solution,
            target_audience=evo.target_audience,
            business_model=evo.business_model,
            tech_stack=evo.tech_stack,
            key_features=evo.key_features,
        ))
        created.append((new_idea, evo.evolution_rationale))

    await db.commit()
    for new_idea, _ in created:
        await db.refresh(new_idea)

    # Judge all evolved ideas concurrently (N × 3 judges in one gather)
    judge_tasks = []
    for new_idea, _ in created:
        d = {
            "id": str(new_idea.id),
            "title": new_idea.title,
            "problem": new_idea.problem,
            "solution": new_idea.solution,
            "target_audience": new_idea.target_audience,
            "business_model": new_idea.business_model,
            "tech_stack": new_idea.tech_stack,
            "key_features": new_idea.key_features or [],
        }
        judge_tasks.extend([
            deps.investor.evaluate(d),
            deps.engineer.evaluate(d),
            deps.skeptic.evaluate(d),
        ])

    all_judge_results = await asyncio.gather(*judge_tasks, return_exceptions=True)

    pid = str(project_id)
    neo4j_batch = []

    for idx, (new_idea, rationale) in enumerate(created):
        chunk = all_judge_results[idx * 3: idx * 3 + 3]
        judges = [JudgeType.INVESTOR, JudgeType.ENGINEER, JudgeType.SKEPTIC]
        scores: list[float] = []
        evals_to_create: list[EvaluationCreate] = []
        for judge_type, jresult in zip(judges, chunk):
            if isinstance(jresult, Exception):
                log.warning("manual_evolve.judge_failed", judge=judge_type.value, error=str(jresult))
                continue
            scores.append(jresult.score)
            evals_to_create.append(EvaluationCreate(
                idea_id=new_idea.id,
                judge_type=judge_type,
                score=jresult.score,
                strengths=jresult.strengths,
                weaknesses=jresult.weaknesses,
                recommendations=jresult.recommendations,
            ))

        if evals_to_create:
            await eval_repo.create_bulk(evals_to_create)

        score_before = idea.score or 5.0
        score_after = round(sum(scores) / len(scores), 2) if scores else score_before
        if scores:
            await idea_repo.update(new_idea.id, IdeaUpdate(score=score_after))

        gt = new_idea.generator_type
        neo4j_batch.append({
            "parent_id": str(idea_id),
            "child_id": str(new_idea.id),
            "project_id": pid,
            "title": new_idea.title,
            "problem": new_idea.problem,
            "solution": new_idea.solution,
            "target_audience": new_idea.target_audience,
            "business_model": new_idea.business_model,
            "tech_stack": new_idea.tech_stack,
            "key_features": new_idea.key_features or [],
            "competitors": idea.competitors or [],
            "generator_type": gt.value if hasattr(gt, "value") else str(gt or ""),
            "rationale": rationale,
            "score_before": score_before,
            "score_after": score_after,
            "score_delta": round(score_after - score_before, 2),
            "aggregate_score": score_after,
        })

    await db.commit()
    for new_idea, _ in created:
        await db.refresh(new_idea)

    # Neo4j write — fails open
    if neo4j_batch:
        try:
            async with neo4j.session() as neo4j_session:
                async def _write_manual_evo(tx):
                    r = await tx.run("""
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
                            c.generator_type  = ev.generator_type,
                            c.aggregate_score = ev.aggregate_score
                        WITH p, c, ev
                        MERGE (p)-[r:EVOLVED_INTO]->(c)
                        SET r.evolution_rationale = ev.rationale,
                            r.score_before        = ev.score_before,
                            r.score_after         = ev.score_after,
                            r.score_delta         = ev.score_delta
                    """, batch=neo4j_batch)
                    await r.consume()
                await neo4j_session.execute_write(_write_manual_evo)
        except Exception as exc:
            log.warning("manual_evolve.neo4j_failed", project_id=pid, error=str(exc))

    log.info("manual_evolve.complete", project_id=pid, idea_id=str(idea_id), count=len(created))
    return [IdeaResponse.model_validate(new_idea) for new_idea, _ in created]


@router.post(
    "/{project_id}/ideas/generate",
    response_model=list[IdeaResponse],
    status_code=status.HTTP_201_CREATED,
)
async def generate_with_constraints(
    project_id: uuid.UUID,
    body: ConstrainedGenerateRequest,
    db: DBSession,
    project_repo: ProjectRepo,
    user_repo: UserRepo,
    idea_repo: IdeaRepo,
    eval_repo: EvaluationRepo,
    report_repo: ReportRepo,
) -> list[IdeaResponse]:
    """Re-generate ideas using all 4 generators, scoped by user-supplied constraints."""
    from ideaforge.api.dependencies import _get_workflow_deps, _get_content_guard
    from ideaforge.domain.enums import GeneratorType
    from ideaforge.guardrails.schemas import ViolationCategory

    deps = _get_workflow_deps()

    # Check the user-supplied constraints before running generators
    cr = await _get_content_guard().check(body.constraints)
    if not cr.safe:
        prefix = (
            "Please clarify your constraints"
            if cr.category == ViolationCategory.AMBIGUOUS
            else f"Constraints not accepted ({cr.category.value.replace('_', ' ').title()})"
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{prefix}: {cr.reason}",
        )

    try:
        project = await _svc(project_repo, user_repo, idea_repo, report_repo).get(project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    augmented = (
        f"{project.problem_statement}\n\n"
        f"=== Additional Constraints from the Founder ===\n{body.constraints}"
    )

    gen_type_map = [
        GeneratorType.CREATIVE,
        GeneratorType.MARKET,
        GeneratorType.BUILDER,
        GeneratorType.ANALYST,
    ]
    gen_results = await asyncio.gather(
        deps.creative.generate(augmented),
        deps.market.generate(augmented),
        deps.builder.generate(augmented),
        deps.analyst.generate(augmented),
        return_exceptions=True,
    )

    raw_ideas: list[tuple] = []
    for gen_type, result in zip(gen_type_map, gen_results):
        if isinstance(result, Exception):
            log.warning("constrained_gen.failed", gen=gen_type.value, error=str(result))
            continue
        for idea_out in result.ideas:
            raw_ideas.append((gen_type, idea_out))

    if not raw_ideas:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="All generators failed — please retry",
        )

    # Guardrail: filter any generated ideas that contain problematic content
    guard = _get_content_guard()
    clean_ideas: list[tuple] = []
    for gen_type, idea_out in raw_ideas:
        idea_text = f"{idea_out.title}. {idea_out.problem}. {idea_out.solution}. {idea_out.business_model}"
        gr = guard.check_sync(idea_text)
        if not gr.safe:
            log.warning(
                "guardrail.constrained_idea_blocked",
                project_id=str(project_id),
                title=idea_out.title[:60],
                category=gr.category,
            )
        else:
            clean_ideas.append((gen_type, idea_out))

    if not clean_ideas:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="All generated ideas were blocked by content guardrails. Please revise your constraints.",
        )
    raw_ideas = clean_ideas

    created: list = []
    for gen_type, idea_out in raw_ideas:
        new_idea = await idea_repo.create(IdeaCreate(
            project_id=project_id,
            generator_type=gen_type,
            title=idea_out.title,
            problem=idea_out.problem,
            solution=idea_out.solution,
            target_audience=idea_out.target_audience,
            business_model=idea_out.business_model,
            tech_stack=idea_out.tech_stack,
            key_features=idea_out.key_features,
            competitors=idea_out.competitors,
        ))
        created.append(new_idea)

    await db.commit()
    for idea in created:
        await db.refresh(idea)

    judge_tasks = []
    for idea in created:
        d = {
            "id": str(idea.id),
            "title": idea.title,
            "problem": idea.problem,
            "solution": idea.solution,
            "target_audience": idea.target_audience,
            "business_model": idea.business_model,
            "tech_stack": idea.tech_stack,
            "key_features": idea.key_features or [],
        }
        judge_tasks.extend([
            deps.investor.evaluate(d),
            deps.engineer.evaluate(d),
            deps.skeptic.evaluate(d),
        ])

    all_results = await asyncio.gather(*judge_tasks, return_exceptions=True)

    for idx, idea in enumerate(created):
        chunk = all_results[idx * 3: idx * 3 + 3]
        judges = [JudgeType.INVESTOR, JudgeType.ENGINEER, JudgeType.SKEPTIC]
        scores: list[float] = []
        evals_to_create: list[EvaluationCreate] = []
        for judge_type, jresult in zip(judges, chunk):
            if isinstance(jresult, Exception):
                log.warning("constrained_gen.judge_failed", judge=judge_type.value, error=str(jresult))
                continue
            scores.append(jresult.score)
            evals_to_create.append(EvaluationCreate(
                idea_id=idea.id,
                judge_type=judge_type,
                score=jresult.score,
                strengths=jresult.strengths,
                weaknesses=jresult.weaknesses,
                recommendations=jresult.recommendations,
            ))
        if evals_to_create:
            await eval_repo.create_bulk(evals_to_create)
        if scores:
            await idea_repo.update(idea.id, IdeaUpdate(score=round(sum(scores) / len(scores), 2)))

    await db.commit()
    for idea in created:
        await db.refresh(idea)

    pid = str(project_id)
    log.info("constrained_gen.complete", project_id=pid, count=len(created))
    return [IdeaResponse.model_validate(idea) for idea in created]


@router.get("/{project_id}/graph", response_model=IdeaGraphResponse)
async def get_idea_graph(
    project_id: uuid.UUID,
    neo4j: Neo4jDriver,
    idea_repo: IdeaRepo,
    eval_repo: EvaluationRepo,
) -> IdeaGraphResponse:
    """Return the full idea lineage graph.

    Always populated from PostgreSQL (guaranteed complete).
    Enriched with Neo4j data (tournament_rank, evolution_rationale, score_delta)
    when available — falls back gracefully if Neo4j is down or partially written.
    """
    pid = str(project_id)

    # ── Step 1: always build from PostgreSQL (authoritative source) ───────────
    db_ideas = await idea_repo.list_by_project(project_id)
    db_evals = await eval_repo.list_by_project(project_id)

    # Score-rank v1 ideas by score descending for approximate tournament_rank
    v1_sorted = sorted(
        [i for i in db_ideas if i.version == 1],
        key=lambda x: (x.score or 0),
        reverse=True,
    )
    db_rank: dict[str, int] = {str(i.id): r for r, i in enumerate(v1_sorted, start=1)}

    nodes: dict[str, IdeaGraphNode] = {
        str(i.id): IdeaGraphNode(
            id=str(i.id),
            title=i.title,
            project_id=pid,
            version=i.version,
            generator_type=i.generator_type.value if hasattr(i.generator_type, "value") else (str(i.generator_type) if i.generator_type else None),
            problem=i.problem,
            solution=i.solution,
            target_audience=i.target_audience,
            business_model=i.business_model,
            tech_stack=i.tech_stack,
            key_features=i.key_features or [],
            competitors=i.competitors or [],
            tournament_rank=db_rank.get(str(i.id)),
            aggregate_score=i.score,
            is_winner=i.is_winner,
        )
        for i in db_ideas
    }

    # EVOLVED_INTO edges from parent_idea_id
    edges: list[IdeaGraphEdge] = [
        IdeaGraphEdge(
            source=str(i.parent_idea_id),
            target=str(i.id),
            type="EVOLVED_INTO",
            score_before=None,
            score_after=i.score,
            score_delta=None,
        )
        for i in db_ideas
        if i.parent_idea_id and i.version > 1
    ]

    # Judge nodes + evaluation edges from evaluations table
    judge_nodes: dict[str, JudgeNode] = {}
    evaluation_edges: list[EvaluationEdge] = []
    for ev in db_evals:
        jtype = ev.judge_type.value if hasattr(ev.judge_type, "value") else str(ev.judge_type)
        judge_id = f"{jtype}_{pid}"
        if judge_id not in judge_nodes:
            judge_nodes[judge_id] = JudgeNode(id=judge_id, judge_type=jtype, project_id=pid)
        evaluation_edges.append(EvaluationEdge(
            source=judge_id,
            target=str(ev.idea_id),
            score=ev.score,
            strengths=ev.strengths or [],
            weaknesses=ev.weaknesses or [],
            recommendations=ev.recommendations or [],
        ))

    # ── Step 2: enrich with Neo4j data where available ────────────────────────
    try:
        async with neo4j.session() as session:
            # Enrich nodes with tournament_rank + aggregate_score from Neo4j
            neo4j_nodes_result = await session.run(
                """
                MATCH (n:Idea {project_id: $pid})
                WHERE n.tournament_rank IS NOT NULL
                RETURN n.id AS id, n.tournament_rank AS rank,
                       n.aggregate_score AS score, n.is_winner AS winner
                """,
                pid=pid,
            )
            for record in await neo4j_nodes_result.data():
                nid = record.get("id", "")
                if nid and nid in nodes:
                    nodes[nid].tournament_rank = record.get("rank")
                    if record.get("score") is not None:
                        nodes[nid].aggregate_score = record["score"]
                    if record.get("winner") is not None:
                        nodes[nid].is_winner = record["winner"]

            # Enrich EVOLVED_INTO edges with rationale + score deltas from Neo4j
            evo_result = await session.run(
                """
                MATCH (p:Idea {project_id: $pid})-[r:EVOLVED_INTO]->(c:Idea {project_id: $pid})
                RETURN p.id AS src, c.id AS tgt,
                       r.evolution_rationale AS rationale,
                       r.score_before AS before, r.score_after AS after,
                       r.score_delta AS delta
                """,
                pid=pid,
            )
            neo4j_evo: dict[tuple, dict] = {}
            for record in await evo_result.data():
                neo4j_evo[(record["src"], record["tgt"])] = record

            for edge in edges:
                if edge.type == "EVOLVED_INTO":
                    neo4j_data = neo4j_evo.get((edge.source, edge.target))
                    if neo4j_data:
                        edge.evolution_rationale = neo4j_data.get("rationale")
                        edge.score_before = neo4j_data.get("before")
                        edge.score_after = neo4j_data.get("after") or edge.score_after
                        edge.score_delta = neo4j_data.get("delta")

            # RANKED_ABOVE edges (only from Neo4j — these aren't in PostgreSQL)
            rank_result = await session.run(
                """
                MATCH (a:Idea {project_id: $pid})-[r:RANKED_ABOVE]->(b:Idea {project_id: $pid})
                RETURN a.id AS a_id, b.id AS b_id, r.score_diff AS diff
                """,
                pid=pid,
            )
            for record in await rank_result.data():
                edges.append(IdeaGraphEdge(
                    source=record["a_id"],
                    target=record["b_id"],
                    type="RANKED_ABOVE",
                    score_diff=record.get("diff"),
                ))

    except Exception as exc:
        log.warning("graph.neo4j_enrichment_skipped", project_id=pid, error=str(exc))

    # Sort nodes by aggregate_score descending so winners appear at top of graph
    sorted_nodes = sorted(
        nodes.values(),
        key=lambda n: (n.tournament_rank or 999, -(n.aggregate_score or 0)),
    )

    return IdeaGraphResponse(
        nodes=sorted_nodes,
        edges=edges,
        judge_nodes=list(judge_nodes.values()),
        evaluation_edges=evaluation_edges,
    )


@router.get("/{project_id}/report", response_model=ReportResponse)
async def get_report(
    project_id: uuid.UUID,
    project_repo: ProjectRepo,
    user_repo: UserRepo,
    idea_repo: IdeaRepo,
    report_repo: ReportRepo,
) -> ReportResponse:
    try:
        report = await _svc(project_repo, user_repo, idea_repo, report_repo).get_report(project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return ReportResponse.model_validate(report)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID,
    db: DBSession,
    project_repo: ProjectRepo,
    neo4j: Neo4jDriver,
) -> None:
    """Permanently delete a project and all its ideas, evaluations, and report."""
    from sqlalchemy import delete as sql_delete, select as sql_select
    from ideaforge.infrastructure.database.models.evaluation import Evaluation
    from ideaforge.infrastructure.database.models.idea import Idea
    from ideaforge.infrastructure.database.models.report import Report as ReportModel
    from ideaforge.infrastructure.database.models.project import Project

    project = await project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    idea_subq = sql_select(Idea.id).where(Idea.project_id == project_id).scalar_subquery()
    await db.execute(sql_delete(Evaluation).where(Evaluation.idea_id.in_(idea_subq)))
    await db.execute(sql_delete(Idea).where(Idea.project_id == project_id))
    await db.execute(sql_delete(ReportModel).where(ReportModel.project_id == project_id))
    await db.execute(sql_delete(Project).where(Project.id == project_id))
    await db.commit()

    pid = str(project_id)
    try:
        async with neo4j.session() as neo4j_session:
            async def _clean(tx):
                await tx.run("MATCH (n:Idea {project_id: $pid}) DETACH DELETE n", pid=pid)
            await neo4j_session.execute_write(_clean)
    except Exception as exc:
        log.warning("delete_project.neo4j_failed", project_id=pid, error=str(exc))

    log.info("project.deleted", project_id=pid)


@router.post("/{project_id}/reset", response_model=ProjectResponse)
async def reset_project(
    project_id: uuid.UUID,
    db: DBSession,
    project_repo: ProjectRepo,
    neo4j: Neo4jDriver,
) -> ProjectResponse:
    """Delete all ideas, evaluations, and report for a project. Reset status to CREATED."""
    from sqlalchemy import delete as sql_delete, select as sql_select
    from ideaforge.infrastructure.database.models.evaluation import Evaluation
    from ideaforge.infrastructure.database.models.idea import Idea
    from ideaforge.infrastructure.database.models.report import Report as ReportModel
    from ideaforge.domain.enums import ProjectStatus

    project = await project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    idea_subq = sql_select(Idea.id).where(Idea.project_id == project_id).scalar_subquery()
    await db.execute(sql_delete(Evaluation).where(Evaluation.idea_id.in_(idea_subq)))
    await db.execute(sql_delete(Idea).where(Idea.project_id == project_id))
    await db.execute(sql_delete(ReportModel).where(ReportModel.project_id == project_id))

    updated = await project_repo.update_status(project_id, ProjectStatus.CREATED)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    await db.commit()
    await db.refresh(updated)

    pid = str(project_id)
    try:
        async with neo4j.session() as neo4j_session:
            async def _clean_neo4j(tx):
                await tx.run(
                    "MATCH (n:Idea {project_id: $pid}) DETACH DELETE n",
                    pid=pid,
                )
            await neo4j_session.execute_write(_clean_neo4j)
    except Exception as exc:
        log.warning("reset.neo4j_clean_failed", project_id=pid, error=str(exc))

    log.info("project.reset", project_id=pid)
    return ProjectResponse.model_validate(updated)
