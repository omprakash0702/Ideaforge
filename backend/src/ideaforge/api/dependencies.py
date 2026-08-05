from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from neo4j import AsyncDriver
from sqlalchemy.ext.asyncio import AsyncSession

from ideaforge.core.config import get_settings
from ideaforge.infrastructure.database.neo4j import get_neo4j_driver
from ideaforge.infrastructure.database.postgres import get_db_session
from ideaforge.infrastructure.repositories.user_repository import SQLUserRepository
from ideaforge.infrastructure.repositories.project_repository import SQLProjectRepository
from ideaforge.infrastructure.repositories.idea_repository import SQLIdeaRepository
from ideaforge.infrastructure.repositories.evaluation_repository import SQLEvaluationRepository
from ideaforge.infrastructure.repositories.report_repository import SQLReportRepository
from ideaforge.agents.evolution import EvolutionAgent
from ideaforge.agents.generators.builder import BuilderFounderAgent
from ideaforge.agents.generators.creative import CreativeFounderAgent
from ideaforge.agents.generators.market import MarketFounderAgent
from ideaforge.agents.generators.analyst import AnalystFounderAgent
from ideaforge.agents.judges.engineer import EngineerJudgeAgent
from ideaforge.agents.judges.investor import InvestorJudgeAgent
from ideaforge.agents.judges.skeptic import SkepticJudgeAgent
from ideaforge.agents.report import ReportAgent
from ideaforge.agents.tournament import TournamentAgent
from ideaforge.application.services.workflow_service import WorkflowService
from ideaforge.guardrails.content_guard import ContentGuard
from ideaforge.rag.document_processor import DocumentProcessor
from ideaforge.rag.embedder import RAGEmbedder
from ideaforge.rag.pipeline import RAGPipeline
from ideaforge.rag.retriever import RAGRetriever
from ideaforge.workflow.deps import WorkflowDeps

# ── Infrastructure aliases ────────────────────────────────────────────────────
DBSession = Annotated[AsyncSession, Depends(get_db_session)]
Neo4jDriver = Annotated[AsyncDriver, Depends(get_neo4j_driver)]


# ── Guardrail — singleton, created once per process ──────────────────────────

@lru_cache
def _get_content_guard() -> ContentGuard:
    settings = get_settings()
    return ContentGuard(api_key=settings.groq_api_key, model=settings.groq_model)


def get_content_guard() -> ContentGuard:
    return _get_content_guard()


Guard = Annotated[ContentGuard, Depends(get_content_guard)]


# ── Repository factory functions ──────────────────────────────────────────────

def get_user_repo(session: AsyncSession = Depends(get_db_session)) -> SQLUserRepository:
    return SQLUserRepository(session)


def get_project_repo(session: AsyncSession = Depends(get_db_session)) -> SQLProjectRepository:
    return SQLProjectRepository(session)


def get_idea_repo(session: AsyncSession = Depends(get_db_session)) -> SQLIdeaRepository:
    return SQLIdeaRepository(session)


def get_evaluation_repo(
    session: AsyncSession = Depends(get_db_session),
) -> SQLEvaluationRepository:
    return SQLEvaluationRepository(session)


def get_report_repo(session: AsyncSession = Depends(get_db_session)) -> SQLReportRepository:
    return SQLReportRepository(session)


# ── RAG pipeline — singleton, created once per process ───────────────────────

@lru_cache
def _get_rag_pipeline() -> RAGPipeline:
    settings = get_settings()
    processor = DocumentProcessor(
        api_key=settings.openai_api_key,
        vision_model=settings.openai_vision_model,
    )
    embedder = RAGEmbedder(
        api_key=settings.openai_api_key,
        embedding_model=settings.openai_embedding_model,
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
    )
    retriever = RAGRetriever(embedder=embedder, top_k=settings.rag_top_k)
    return RAGPipeline(processor=processor, embedder=embedder, retriever=retriever)


def get_rag_pipeline() -> RAGPipeline:
    return _get_rag_pipeline()


RAG = Annotated[RAGPipeline, Depends(get_rag_pipeline)]


# ── Workflow dependencies — all agent singletons ──────────────────────────────

@lru_cache
def _get_workflow_deps() -> WorkflowDeps:
    settings = get_settings()
    rag = _get_rag_pipeline()
    return WorkflowDeps(
        creative=CreativeFounderAgent(api_key=settings.google_api_key, model=settings.gemini_model),
        market=MarketFounderAgent(api_key=settings.google_api_key, model=settings.gemini_model),
        builder=BuilderFounderAgent(api_key=settings.google_api_key, model=settings.gemini_model),
        analyst=AnalystFounderAgent(api_key=settings.openai_api_key, model=settings.openai_model),
        investor=InvestorJudgeAgent(api_key=settings.openai_api_key, model=settings.openai_model),
        engineer=EngineerJudgeAgent(api_key=settings.openai_api_key, model=settings.openai_model),
        skeptic=SkepticJudgeAgent(api_key=settings.openai_api_key, model=settings.openai_model),
        evolution=EvolutionAgent(api_key=settings.openai_api_key, model=settings.openai_model),
        tournament=TournamentAgent(),
        report_agent=ReportAgent(api_key=settings.openai_api_key, model=settings.openai_model),
        rag=rag,
        guard=_get_content_guard(),
    )


@lru_cache
def _get_workflow_service() -> WorkflowService:
    return WorkflowService(deps=_get_workflow_deps())


def get_workflow_service() -> WorkflowService:
    return _get_workflow_service()


# ── Typed aliases for route handler signatures ────────────────────────────────
UserRepo = Annotated[SQLUserRepository, Depends(get_user_repo)]
ProjectRepo = Annotated[SQLProjectRepository, Depends(get_project_repo)]
IdeaRepo = Annotated[SQLIdeaRepository, Depends(get_idea_repo)]
EvaluationRepo = Annotated[SQLEvaluationRepository, Depends(get_evaluation_repo)]
ReportRepo = Annotated[SQLReportRepository, Depends(get_report_repo)]
