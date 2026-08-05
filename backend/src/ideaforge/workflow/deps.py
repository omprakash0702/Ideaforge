from dataclasses import dataclass

from ideaforge.agents.generators.creative import CreativeFounderAgent
from ideaforge.agents.generators.market import MarketFounderAgent
from ideaforge.agents.generators.builder import BuilderFounderAgent
from ideaforge.agents.generators.analyst import AnalystFounderAgent
from ideaforge.agents.judges.investor import InvestorJudgeAgent
from ideaforge.agents.judges.engineer import EngineerJudgeAgent
from ideaforge.agents.judges.skeptic import SkepticJudgeAgent
from ideaforge.agents.evolution import EvolutionAgent
from ideaforge.agents.tournament import TournamentAgent
from ideaforge.agents.report import ReportAgent
from ideaforge.guardrails.content_guard import ContentGuard
from ideaforge.rag.pipeline import RAGPipeline


@dataclass
class WorkflowDeps:
    """All stateless agent singletons needed by the LangGraph workflow."""

    creative: CreativeFounderAgent
    market: MarketFounderAgent
    builder: BuilderFounderAgent
    analyst: AnalystFounderAgent
    investor: InvestorJudgeAgent
    engineer: EngineerJudgeAgent
    skeptic: SkepticJudgeAgent
    evolution: EvolutionAgent
    tournament: TournamentAgent
    report_agent: ReportAgent
    rag: RAGPipeline
    guard: ContentGuard
