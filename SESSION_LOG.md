# IdeaForge — Development Session Log

A running record of major decisions, changes, fixes, and deployment work done across all Claude sessions.

---

## Session 1 — Foundation & Milestone 1

### What was built
- Project scaffolding: FastAPI backend, Next.js frontend, LangGraph workflow
- Database layer: PostgreSQL with SQLAlchemy async + Alembic migrations
- 4 generator agents: Visionary, Strategist, Architect, Analyst (OpenAI + Gemini)
- 3 judge agents: Investor, Engineer, Skeptic (OpenAI)
- Evolution engine: low-scoring ideas improved using judge feedback
- Tournament engine: all ideas ranked, single winner selected
- Report generator: concise markdown summary of the winning idea
- FastAPI integration: all workflow stages exposed as REST endpoints
- Neo4j lineage graph: idea evolution stored as a directed graph
- Content guardrails: keyword filter (Tier 1) + Groq LLM semantic check (Tier 2)
- Frontend dashboard: project list, project detail with 6 tabs (Overview, Ideas, Evaluations, Graph, Report, Analytics)

### LLM routing decisions
| Provider | Model | Used for |
|---|---|---|
| OpenAI | gpt-4o-mini | Analyst agent, all 3 judges, evolution, report, embeddings |
| Google Gemini | gemini-2.5-flash | Creative, Market, Builder generators |
| Groq | llama-3.3-70b-versatile | Content guardrail semantic check |

### Key files
- `backend/src/ideaforge/workflow/nodes.py` — all LangGraph node definitions
- `backend/src/ideaforge/workflow/state.py` — shared state TypedDict
- `backend/src/ideaforge/agents/` — generator, judge, evolution, report agents
- `frontend/src/app/` — Next.js pages

---

## Session 2 — RAG, Guardrails, Frontend Polish

### What was built
- RAG pipeline: document upload → chunk → embed (OpenAI) → store in pgvector → inject context into generators
- History tab with clear history option
- Report rewrite: removed execution plans and roadmaps; replaced with concise summary (what won, why, risks, one next step)
- Analytics panel added to frontend

### Key decision: ChromaDB chosen initially for vector store
- ChromaDB stores embeddings in a local directory (chroma_db/)
- This works fine locally but becomes a problem for cloud deployment (Cloud Run containers lose disk state on restart)

---

## Session 3 — GCP Deployment

### Problem: ChromaDB is stateless on Cloud Run
**Decision:** Migrate ChromaDB → pgvector (store embeddings directly in PostgreSQL/Cloud SQL).
- pgvector persists forever in Cloud SQL
- One less service to manage
- No file system dependency

### ChromaDB → pgvector migration
**Files changed:**
- `backend/src/ideaforge/rag/embedder.py` — full rewrite: OpenAI batched embeddings, DELETE by doc_hash before INSERT, `<=>` cosine distance operator for similarity search
- `backend/alembic/versions/0003_add_pgvector.py` — creates `document_chunks` table with `vector(1536)` column + IVFFlat index
- `backend/src/ideaforge/core/config.py` — removed `chroma_persist_dir`
- `backend/src/ideaforge/api/dependencies.py` — removed `persist_dir` arg
- `backend/pyproject.toml` — removed `chromadb`, `langchain-chroma`; added `pgvector>=0.3.0`

### Redis removal
Redis was only used in the health check ping — it wasn't caching or queuing anything real.
- Removed `redis[hiredis]` from dependencies
- Deleted `backend/src/ideaforge/infrastructure/cache/redis.py`
- Removed Redis from `docker-compose.yml`
- Updated health check to only probe PostgreSQL + Neo4j

### GCP services created

#### Artifact Registry
```
asia-south1-docker.pkg.dev/talentscout-ai-001/ideaforge/
  ├── backend:latest
  └── frontend:latest
```

#### Cloud SQL (PostgreSQL 15)
- Instance: `ideaforge-db`, tier: `db-f1-micro`, region: `asia-south1`
- pgvector extension enabled
- 3 Alembic migrations applied
- Connected to Cloud Run via Unix socket (no public IP)

#### GCE VM (Neo4j)
- VM: `ideaforge-neo4j`, zone: `asia-south1-b`, machine: `e2-micro`
- Neo4j Community Edition installed via startup script
- External IP: `34.93.157.66`
- Ports: 7474 (browser), 7687 (bolt)
- Firewall rule: `allow-neo4j` targeting tag `neo4j-server`
- Password: stored in Secret Manager as `neo4j-password`

**Why a VM instead of Cloud Run for Neo4j?**
Neo4j writes data to disk. Cloud Run containers are ephemeral — disk is lost on restart. A GCE VM keeps its disk across reboots.

#### Secret Manager secrets
| Secret | Value |
|---|---|
| `database-url` | PostgreSQL connection string with Unix socket |
| `neo4j-uri` | `bolt://34.93.157.66:7687` |
| `neo4j-username` | `neo4j` |
| `neo4j-password` | `IdeaForge_N4j_2025!` |
| `openai-api-key` | sk-... |
| `google-api-key` | AIza... |
| `groq-api-key` | gsk_... |
| `allowed-origins` | Frontend Cloud Run URL |

#### Cloud Run — Backend
- Service: `ideaforge-backend`
- URL: `https://ideaforge-backend-1006031252410.asia-south1.run.app`
- `min-instances=1` to avoid cold start delays
- Cloud SQL connection: `talentscout-ai-001:asia-south1:ideaforge-db`

#### Cloud Run — Frontend
- Service: `ideaforge-frontend`
- URL: `https://ideaforge-frontend-1006031252410.asia-south1.run.app`
- `min-instances=0` (scales to zero when idle)
- `NEXT_PUBLIC_API_URL` baked in at Docker build time

### Errors encountered and fixed

| Error | Fix |
|---|---|
| Zone `asia-south1-a` had no `e2-micro` capacity | Used `asia-south1-b` instead |
| Password generation: `python3` not available in Bash | Used PowerShell to generate passwords |
| Frontend Docker build failed: `public/` dir missing | Changed `COPY --from=builder /app/public ./public` to `RUN mkdir -p ./public` |
| Cloud SQL can't fully disable public IP | Cleared authorized networks with `--clear-authorized-networks` instead |
| Cloud Build trigger setup required GitHub OAuth in browser | Skipped CI/CD; manual redeploy process documented instead |
| CORS was hardcoded to localhost | Made `allowed_origins` an env var, split by comma in `main.py`, stored in Secret Manager |

### CORS fix
`backend/src/ideaforge/main.py`:
```python
origins = settings.allowed_origins.split(",") if settings.allowed_origins else []
app.add_middleware(CORSMiddleware, allow_origins=origins, ...)
```

### Frontend standalone Docker fix
`frontend/next.config.ts`:
```typescript
output: 'standalone'
```
`frontend/Dockerfile`:
```dockerfile
FROM node:22-alpine AS runner
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
RUN mkdir -p ./public   # public/ may not exist if no static assets
```

---

## Session 4 — Speed Optimization & Neo4j Fix

### Problem: Execution speed slow in cloud
Three causes identified:

**1. Cold starts (fixed)**
- Backend was `min-instances=0`; first request after idle takes ~8-10s to start the container
- Fix: set `min-instances=1` via `gcloud run services update`

**2. Web search blocking idea generation (fixed in code, deployed in this session)**
- DuckDuckGo search was called sequentially *before* generators ran
- Fix: moved search to `rag_fetch` node so it runs in parallel with RAG retrieval
- Timeout reduced from 15s to 5s (GCP IPs are sometimes rate-limited by DDG)

`backend/src/ideaforge/workflow/state.py` — added:
```python
web_context: NotRequired[str]  # live market research from DuckDuckGo
```

`backend/src/ideaforge/workflow/nodes.py` — rag_fetch now:
```python
rag_task = asyncio.create_task(deps.rag.get_context(project_id, problem))
web_task = asyncio.create_task(_web_search(search_query))
rag_ctx, web_ctx = await asyncio.gather(rag_task, web_task, return_exceptions=True)
return {"rag_context": rag_text, "web_context": web_ctx or ""}
```

**3. DuckDuckGo rate limiting from GCP IPs**
- Mitigated by 5s timeout: workflow proceeds with empty web context if DDG is slow/blocked

### Problem: Workflow hanging at "Running tournament"
**Root cause:** Neo4j VM had a broken network state on first boot — the GCP metadata server (169.254.169.254) was unreachable, which meant the startup script never ran and Neo4j was never installed.

**Symptoms:**
- `http://34.93.157.66:7474` not opening
- SSH timing out ("Remote side unexpectedly closed network connection")
- Serial console showed only metadata server errors, no Neo4j install output

**Fix:**
```bash
gcloud compute instances reset ideaforge-neo4j --zone=asia-south1-b --project=talentscout-ai-001
```
After reset, the startup script ran on boot and Neo4j installed and started successfully.
Confirmed via serial console: `2026-08-06 13:18:04.840 INFO Started.`

**Verification:**
```powershell
Test-NetConnection -ComputerName 34.93.157.66 -Port 7474  # True
Test-NetConnection -ComputerName 34.93.157.66 -Port 7687  # True
```

Neo4j browser now opens at `http://34.93.157.66:7474`.
Bolt password in Secret Manager matches startup script: `IdeaForge_N4j_2025!` ✅

### Docs update
- `README.md` — Work in Progress section expanded: user auth (JWT) and RAG upload UI added as explicit WIP items
- `CLOUD.md` — new file: full GCP deployment guide in plain language

---

## Current Live State

| Component | Status | URL / Location |
|---|---|---|
| Frontend | ✅ Live | https://ideaforge-frontend-1006031252410.asia-south1.run.app |
| Backend API | ✅ Live | https://ideaforge-backend-1006031252410.asia-south1.run.app |
| API Docs | ✅ Live | https://ideaforge-backend-1006031252410.asia-south1.run.app/docs |
| PostgreSQL | ✅ Live | Cloud SQL `ideaforge-db`, asia-south1 |
| Neo4j | ✅ Live | GCE VM `ideaforge-neo4j`, 34.93.157.66 |
| GitHub | ✅ Pushed | https://github.com/omprakash0702/Ideaforge |

---

## What Is Still Pending

| Item | Notes |
|---|---|
| User authentication | No login system; projects accessible by ID. JWT needed before public launch. |
| RAG frontend UI | Backend supports document uploads; no UI to trigger it yet. |
| Rate limiting | No per-user limits; one run = ~20 LLM calls across 3 providers. |
| Test coverage | Repository-layer tests exist; agent + workflow tests not written. |
| Error boundaries | No React error boundaries in frontend. |
| Pagination | List endpoints return all rows; will slow at scale. |

---

## Redeploy Commands (Quick Reference)

```bash
# Backend
docker build --target=prod -t asia-south1-docker.pkg.dev/talentscout-ai-001/ideaforge/backend:latest backend/
docker push asia-south1-docker.pkg.dev/talentscout-ai-001/ideaforge/backend:latest
gcloud run deploy ideaforge-backend --image=asia-south1-docker.pkg.dev/talentscout-ai-001/ideaforge/backend:latest --region=asia-south1 --project=talentscout-ai-001

# Frontend
docker build --build-arg NEXT_PUBLIC_API_URL=https://ideaforge-backend-1006031252410.asia-south1.run.app/api/v1 -t asia-south1-docker.pkg.dev/talentscout-ai-001/ideaforge/frontend:latest frontend/
docker push asia-south1-docker.pkg.dev/talentscout-ai-001/ideaforge/frontend:latest
gcloud run deploy ideaforge-frontend --image=asia-south1-docker.pkg.dev/talentscout-ai-001/ideaforge/frontend:latest --region=asia-south1 --project=talentscout-ai-001

# Restart Neo4j if it stops responding
gcloud compute instances reset ideaforge-neo4j --zone=asia-south1-b --project=talentscout-ai-001
```
