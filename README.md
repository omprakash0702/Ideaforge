# IdeaForge

AI-powered startup idea simulator. Describe a problem — four AI founders generate ideas, three AI judges score them, weak ideas evolve, a tournament picks a winner, and you get a concise summary of why it won.

---

## How It Works

1. **Generate** — 4 AI founders (Visionary, Strategist, Architect, Analyst) independently generate startup ideas for your problem
2. **Judge** — 3 AI judges (Investor, Engineer, Skeptic) score every idea on market fit, feasibility, and risk
3. **Evolve** — Low-scoring ideas are improved using judge feedback as signal
4. **Tournament** — All ideas (original + evolved) compete; one winner is selected
5. **Report** — The winner gets a concise summary: what it is, why it beat the others, real risks, one concrete next step
6. **Graph** — Full idea lineage visualized as an interactive evolution graph

Every input runs through two-tier content guardrails: instant keyword filter + Groq LLM semantic check.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Python 3.12, LangGraph |
| Primary DB | PostgreSQL 15 + pgvector (SQLAlchemy async + Alembic) |
| Graph DB | Neo4j (idea lineage + ranking) |
| Vector store | pgvector — document chunks stored in PostgreSQL |
| Frontend | Next.js 15, TypeScript, Tailwind CSS |
| LLMs | OpenAI GPT-4o-mini · Google Gemini 2.5 Flash · Groq Llama 3.3 |
| Deployment | GCP Cloud Run · Cloud SQL · GCE (Neo4j) |

---

## Project Structure

```
IdeaForge/
├── backend/
│   ├── src/ideaforge/
│   │   ├── agents/         # LLM agents — generators, judges, evolution, report
│   │   ├── api/            # FastAPI routes, schemas, dependencies
│   │   ├── application/    # Service layer (use-cases)
│   │   ├── core/           # Config, logging, exceptions
│   │   ├── domain/         # Interfaces, enums
│   │   ├── guardrails/     # Two-tier content moderation
│   │   ├── infrastructure/ # PostgreSQL + Neo4j + repositories
│   │   ├── rag/            # Document upload → pgvector → context retrieval
│   │   └── workflow/       # LangGraph graph, nodes, state
│   ├── alembic/            # DB migrations
│   ├── tests/
│   ├── Dockerfile
│   └── docker-compose.yml
├── frontend/
│   ├── src/
│   │   ├── app/            # Pages: project list, project detail (6 tabs)
│   │   ├── components/     # IdeaCard, IdeaGraph, ReportView, AnalyticsPanel
│   │   └── lib/            # API client, utils
│   └── Dockerfile
└── docs/                   # Architecture, data model, API, agent design docs
```

---

## Local Setup

### Prerequisites

| Tool | Version |
|---|---|
| Python | 3.12+ |
| uv | latest — `pip install uv` |
| Node.js | 20+ |
| Docker + Compose V2 | latest |

### Backend

```bash
cd backend
cp .env.example .env
# Fill in: OPENAI_API_KEY, GOOGLE_API_KEY, GROQ_API_KEY

docker compose up -d           # starts PostgreSQL + Neo4j
uv sync
uv run alembic upgrade head
uv run uvicorn ideaforge.main:app --reload
```

| URL | |
|---|---|
| API | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |
| Neo4j Browser | http://localhost:7474 |

### Frontend

```bash
cd frontend
cp .env.local.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

npm install
npm run dev
```

App: http://localhost:3000

---

## API Reference

Base URL: `/api/v1`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/projects` | Create project |
| POST | `/projects/{id}/run` | Run full workflow |
| GET | `/projects/{id}` | Project status |
| GET | `/projects/{id}/ideas` | All ideas |
| GET | `/projects/{id}/evaluations` | Judge scores |
| GET | `/projects/{id}/report` | Final summary |
| GET | `/projects/{id}/graph` | Lineage graph |
| POST | `/projects/{id}/documents` | Upload document for RAG |
| POST | `/projects/{id}/reset` | Reset project to CREATED |
| DELETE | `/projects/{id}` | Delete project |
| POST | `/users` | Create user |
| GET | `/users/{id}/projects` | User project history |
| GET | `/health` | Liveness check |
| GET | `/health/ready` | Readiness — probes PostgreSQL + Neo4j |

Full interactive schema: http://localhost:8000/docs

---

## LLM Providers

| Provider | Model | Used For |
|---|---|---|
| OpenAI | `gpt-4o-mini` | Analyst agent, all 3 judges, evolution, report, embeddings |
| Google Gemini | `gemini-2.5-flash` | Creative, Market, Builder generators |
| Groq | `llama-3.3-70b-versatile` | Content guardrail (Tier 2 semantic check) |

---

## Environment Variables

Copy `backend/.env.example` → `backend/.env` and fill in:

```env
# Required
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
GROQ_API_KEY=gsk_...

# Defaults work for local Docker Compose
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ideaforge
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
```

Copy `frontend/.env.local.example` → `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## Database Migrations

```bash
uv run alembic upgrade head                           # apply all migrations
uv run alembic revision --autogenerate -m "message"  # create new migration
uv run alembic downgrade -1                           # roll back one step
```

---

## Tests

```bash
cd backend
uv run pytest                  # all tests
uv run pytest -m "not llm"    # skip tests that make real LLM calls
uv run pytest -m "not db"     # skip tests that need a live database
```

---

## Content Guardrails

Two-tier — runs on every user input before anything is saved:

- **Tier 1** — Keyword regex filter (instant, zero API cost)
- **Tier 2** — Groq LLM semantic check (~500ms). Catches indirect violations like coded markets, euphemistic scams, disguised adult platforms

Fail-open: if Groq is unavailable, Tier 2 is skipped and Tier 1 still applies.

---

## Live URLs

| | URL |
|---|---|
| **Frontend** | https://ideaforge-frontend-1006031252410.asia-south1.run.app |
| **Backend API** | https://ideaforge-backend-1006031252410.asia-south1.run.app |
| **Swagger docs** | https://ideaforge-backend-1006031252410.asia-south1.run.app/docs |

---

## Deployment

| Component | Platform | Details |
|---|---|---|
| Frontend | GCP Cloud Run | `asia-south1`, scales to 0 |
| Backend | GCP Cloud Run | `asia-south1`, scales to 0 |
| PostgreSQL + pgvector | GCP Cloud SQL | PostgreSQL 15, `db-f1-micro`, `asia-south1` |
| Neo4j | GCP GCE | `e2-micro`, `asia-south1-b`, Community Edition |
| Secrets | GCP Secret Manager | API keys, DB URL, Neo4j credentials |
| Images | GCP Artifact Registry | `asia-south1-docker.pkg.dev/talentscout-ai-001/ideaforge` |

CI/CD: Connect GitHub repo in [GCP Cloud Build Console](https://console.cloud.google.com/cloud-build/triggers) → trigger on push to `main` → `cloudbuild.yaml` handles build + migrate + deploy automatically.

---

## Status

| Milestone | Status |
|---|---|
| Project foundation | ✅ Done |
| Database layer (PostgreSQL + Neo4j) | ✅ Done |
| LangGraph workflow engine | ✅ Done |
| Generator agents (4 founders) | ✅ Done |
| Judge agents (3 judges) | ✅ Done |
| Evolution engine | ✅ Done |
| Tournament engine | ✅ Done |
| Report generator | ✅ Done |
| FastAPI integration | ✅ Done |
| Frontend dashboard | ✅ Done |
| Neo4j idea lineage graph | ✅ Done |
| RAG — document context (pgvector) | ✅ Done |
| Content guardrails | ✅ Done |
| GCP deployment | ✅ Done |
| Testing | Partial |
