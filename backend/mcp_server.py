#!/usr/bin/env python3
"""IdeaForge MCP server.

Exposes the IdeaForge REST API as MCP tools so Claude Desktop (or any
MCP-compatible client) can create projects, trigger the AI workflow,
poll for status, and read the final report — all from a conversation.

Usage
-----
Run as a stdio server (Claude Desktop):
    python mcp_server.py

Environment variables
---------------------
IDEAFORGE_API_URL   Base URL of the running FastAPI backend.
                    Default: http://localhost:8000/api/v1

Claude Desktop config (~/.claude_desktop_config.json)
------------------------------------------------------
{
  "mcpServers": {
    "ideaforge": {
      "command": "python",
      "args": ["/absolute/path/to/backend/mcp_server.py"],
      "env": {
        "IDEAFORGE_API_URL": "http://localhost:8000/api/v1"
      }
    }
  }
}
"""

import os
import httpx
from mcp.server.fastmcp import FastMCP

_BASE = os.getenv("IDEAFORGE_API_URL", "http://localhost:8000/api/v1")

mcp = FastMCP(
    "IdeaForge",
    version="0.1.0",
    description=(
        "AI-powered Startup Survival Simulator. "
        "Create a project, run the multi-agent workflow, and get a full startup report."
    ),
)


# ── Helper ────────────────────────────────────────────────────────────────────

def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=_BASE, timeout=30.0)


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
async def create_user(name: str, email: str) -> dict:
    """Create a user account.

    Returns the user object including `id`, which is required for create_project.
    """
    async with _client() as c:
        r = await c.post("/users", json={"name": name, "email": email})
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def create_project(user_id: str, title: str, problem_statement: str) -> dict:
    """Create a new IdeaForge project.

    Args:
        user_id: UUID string from create_user.
        title: Short human-readable project name.
        problem_statement: The startup problem to explore (1–3 paragraphs).
                           Clearer = better ideas. Rejected if harmful.

    Returns the project object including `id`, needed for run_workflow.
    """
    async with _client() as c:
        r = await c.post(
            "/projects",
            json={
                "user_id": user_id,
                "title": title,
                "problem_statement": problem_statement,
            },
        )
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def run_workflow(project_id: str) -> dict:
    """Start the IdeaForge AI workflow for a project.

    Returns immediately with status=RUNNING (202 Accepted).
    The pipeline runs in the background: web search → generate (3 LLMs) →
    judge (3 panels) → evolve → tournament → report.

    Poll get_project_status until status is COMPLETED or FAILED (~2–4 min).
    """
    async with _client() as c:
        r = await c.post(f"/projects/{project_id}/run")
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def get_project_status(project_id: str) -> dict:
    """Get the current project including its status.

    Status lifecycle:
      CREATED → RUNNING → GENERATING → JUDGING → EVOLVING
              → TOURNAMENT → REPORTING → COMPLETED
      Any stage can transition to FAILED.
    """
    async with _client() as c:
        r = await c.get(f"/projects/{project_id}")
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def get_ideas(project_id: str) -> list:
    """List all generated ideas for a project.

    Includes original ideas from all 3 generator agents plus any evolved
    variants. Each idea has title, solution, business_model, tech_stack,
    score, is_winner, and generator_type.
    """
    async with _client() as c:
        r = await c.get(f"/projects/{project_id}/ideas")
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def get_report(project_id: str) -> str:
    """Get the final markdown startup report for a completed project.

    Contains: Executive Summary, Market Opportunity, 90-Day Technical Roadmap,
    GTM Strategy, Financial Projections, Team Structure, Risk Mitigation,
    and why the winning idea beats the competition.

    Only available when project status is COMPLETED.
    """
    async with _client() as c:
        r = await c.get(f"/projects/{project_id}/report")
        r.raise_for_status()
        return r.json().get("markdown_report", "")


@mcp.tool()
async def get_idea_graph(project_id: str) -> dict:
    """Get the idea lineage graph from Neo4j.

    Returns nodes (all ideas with tournament rank and score) and
    edges (EVOLVED_INTO relationships showing which ideas were improved
    from lower-scoring originals).

    Only populated after the workflow reaches the evolve stage.
    """
    async with _client() as c:
        r = await c.get(f"/projects/{project_id}/graph")
        r.raise_for_status()
        return r.json()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()  # stdio transport — compatible with Claude Desktop
