# IdeaForge — Cloud Deployment Guide

This document explains how IdeaForge is deployed on Google Cloud Platform (GCP), what each service does, and how to redeploy after making changes.

---

## GCP Project

| Field | Value |
|---|---|
| Project ID | `talentscout-ai-001` |
| Region | `asia-south1` (Mumbai) |

Always pass `--project=talentscout-ai-001` in every `gcloud` command so you don't accidentally affect other GCP projects.

---

## Architecture Overview

```
Browser
  │
  └─► Cloud Run: Frontend (Next.js)
          │
          └─► Cloud Run: Backend (FastAPI)
                    │
                    ├─► Cloud SQL: PostgreSQL + pgvector  (ideas, users, embeddings)
                    └─► GCE VM: Neo4j                     (idea lineage graph)
```

- **Cloud Run** — fully managed containers; auto-scales to zero when no traffic
- **Cloud SQL** — managed PostgreSQL; handles the main database and vector search
- **GCE VM** — a small Linux VM running Neo4j (needed because Neo4j can't run as a stateless container)
- **Secret Manager** — stores all API keys and passwords; containers read them at startup
- **Artifact Registry** — stores the Docker images that Cloud Run pulls

---

## Services Set Up

### 1. Artifact Registry

Stores Docker images for both services.

```
Registry path: asia-south1-docker.pkg.dev/talentscout-ai-001/ideaforge/
  ├── backend:latest
  └── frontend:latest
```

**Created with:**
```bash
gcloud artifacts repositories create ideaforge \
  --repository-format=docker \
  --location=asia-south1 \
  --project=talentscout-ai-001
```

---

### 2. Cloud SQL — PostgreSQL

Runs the main database (projects, ideas, evaluations, users, document embeddings).

| Setting | Value |
|---|---|
| Instance name | `ideaforge-db` |
| Database | `ideaforge` |
| User | `ideaforge` |
| Tier | `db-f1-micro` (cheapest, enough for low traffic) |
| Region | `asia-south1` |
| Extensions | `pgvector` (for storing and searching embeddings) |

The backend connects via a **Unix socket** (not TCP). Cloud Run automatically creates a socket at `/cloudsql/talentscout-ai-001:asia-south1:ideaforge-db`. This is more secure than exposing a public IP.

Database migrations are run with Alembic:
```bash
uv run alembic upgrade head
```

Three migrations have been applied:
- `0001` — base tables (projects, users, ideas, evaluations)
- `0002` — tournament results, report storage
- `0003` — pgvector extension + document_chunks table

---

### 3. GCE VM — Neo4j

Neo4j is used to store the idea lineage graph (which idea evolved from which, tournament rankings).

| Setting | Value |
|---|---|
| VM name | `ideaforge-neo4j` |
| Zone | `asia-south1-b` |
| Machine type | `e2-micro` (1 vCPU, 1 GB RAM) |
| OS | Ubuntu 22.04 LTS |
| External IP | `34.93.157.66` (static) |
| Bolt port | `7687` (used by backend) |
| Browser port | `7474` (admin UI) |

**Why a VM and not Cloud Run?** Neo4j stores its data on disk. Cloud Run containers are stateless — any data stored inside them is lost on restart. A VM keeps its disk across reboots.

**Startup script** (runs on every boot, installs Neo4j automatically):
```bash
apt-get install -y openjdk-21-jre neo4j
neo4j-admin dbms set-initial-password IdeaForge_N4j_2025!
# bind to all network interfaces so the backend can reach it
sed -i 's/#server.default_listen_address=0.0.0.0/server.default_listen_address=0.0.0.0/' /etc/neo4j/neo4j.conf
systemctl enable neo4j && systemctl start neo4j
```

**Firewall rule** (allows traffic on Neo4j ports):
```bash
gcloud compute firewall-rules create allow-neo4j \
  --allow tcp:7687,tcp:7474 \
  --target-tags neo4j-server \
  --project=talentscout-ai-001
```

**Admin UI:** Open `http://34.93.157.66:7474` in your browser.
- Username: `neo4j`
- Password: `IdeaForge_N4j_2025!`

**Troubleshooting:** If Neo4j stops responding, SSH into the VM and check:
```bash
sudo systemctl status neo4j
sudo systemctl restart neo4j
```
Or reset the VM from GCP Console → Compute Engine → VM Instances → Reset.

---

### 4. Secret Manager

All sensitive values are stored here instead of in code or environment files.

| Secret name | What it stores |
|---|---|
| `database-url` | Full PostgreSQL connection string (used by backend Cloud Run) |
| `neo4j-uri` | `bolt://34.93.157.66:7687` |
| `neo4j-username` | `neo4j` |
| `neo4j-password` | `IdeaForge_N4j_2025!` |
| `openai-api-key` | OpenAI key (generators, judges, embeddings) |
| `google-api-key` | Google Gemini key (Creative, Market, Builder agents) |
| `groq-api-key` | Groq key (content guardrail tier-2 check) |
| `allowed-origins` | CORS whitelist (frontend Cloud Run URL) |

To update a secret value:
```bash
echo -n "new-value" | gcloud secrets versions add SECRET_NAME \
  --data-file=- --project=talentscout-ai-001
```

---

### 5. Cloud Run — Backend (FastAPI)

Runs the Python FastAPI app that handles all API requests and the LangGraph workflow.

| Setting | Value |
|---|---|
| Service name | `ideaforge-backend` |
| URL | `https://ideaforge-backend-1006031252410.asia-south1.run.app` |
| Min instances | `1` (keeps one container warm; avoids cold start delays) |
| Max instances | `5` |
| Memory | `1Gi` |
| CPU | `1` |
| Concurrency | `80` |
| Cloud SQL connection | `talentscout-ai-001:asia-south1:ideaforge-db` |

Secrets are injected as environment variables at startup — the container never sees raw values in its config.

**To redeploy backend after code changes:**
```bash
# 1. Build new Docker image
docker build --target=prod \
  -t asia-south1-docker.pkg.dev/talentscout-ai-001/ideaforge/backend:latest \
  backend/

# 2. Push to Artifact Registry
docker push asia-south1-docker.pkg.dev/talentscout-ai-001/ideaforge/backend:latest

# 3. Deploy to Cloud Run
gcloud run deploy ideaforge-backend \
  --image=asia-south1-docker.pkg.dev/talentscout-ai-001/ideaforge/backend:latest \
  --region=asia-south1 \
  --project=talentscout-ai-001
```

---

### 6. Cloud Run — Frontend (Next.js)

Runs the Next.js app. Built with `output: 'standalone'` so it works as a Docker container.

| Setting | Value |
|---|---|
| Service name | `ideaforge-frontend` |
| URL | `https://ideaforge-frontend-1006031252410.asia-south1.run.app` |
| Min instances | `0` (scales to zero; lower cost) |
| Memory | `512Mi` |

The backend API URL is baked in at build time as a Docker build argument:
```
NEXT_PUBLIC_API_URL=https://ideaforge-backend-1006031252410.asia-south1.run.app/api/v1
```

**To redeploy frontend after code changes:**
```bash
# 1. Build
docker build \
  --build-arg NEXT_PUBLIC_API_URL=https://ideaforge-backend-1006031252410.asia-south1.run.app/api/v1 \
  -t asia-south1-docker.pkg.dev/talentscout-ai-001/ideaforge/frontend:latest \
  frontend/

# 2. Push
docker push asia-south1-docker.pkg.dev/talentscout-ai-001/ideaforge/frontend:latest

# 3. Deploy
gcloud run deploy ideaforge-frontend \
  --image=asia-south1-docker.pkg.dev/talentscout-ai-001/ideaforge/frontend:latest \
  --region=asia-south1 \
  --project=talentscout-ai-001
```

---

## Cost Estimate (approximate)

| Service | Tier | Est. monthly cost |
|---|---|---|
| Cloud Run (backend, min 1) | ~720 instance-hours/month | ~$5–8 |
| Cloud Run (frontend, min 0) | Scales to zero | ~$0–2 |
| Cloud SQL | `db-f1-micro` | ~$7–10 |
| GCE VM (Neo4j) | `e2-micro` | ~$6–8 |
| Secret Manager | First 6 secrets free | ~$0 |
| Artifact Registry | First 0.5 GB free | ~$0 |
| **Total** | | **~$18–28/month** |

Setting `min-instances=0` on the backend would reduce cost but causes a ~5-10 second cold start delay on the first request after idle time.

---

## Common Operations

### Check if backend is healthy
```
GET https://ideaforge-backend-1006031252410.asia-south1.run.app/health/ready
```
Returns `{"status": "ok"}` if PostgreSQL and Neo4j are both reachable.

### Run database migrations on Cloud SQL
Connect via Cloud SQL Auth Proxy locally and run Alembic, or temporarily run from the backend Cloud Run container.

### View Cloud Run logs
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ideaforge-backend" \
  --limit=50 --project=talentscout-ai-001 --format="table(timestamp,textPayload)"
```

### Restart Neo4j VM (if hanging)
```bash
gcloud compute instances reset ideaforge-neo4j \
  --zone=asia-south1-b --project=talentscout-ai-001
```
Neo4j takes about 10 minutes to reinstall on first reset (startup script runs apt-get). On subsequent resets it starts in ~2 minutes.

---

## What Was Migrated / Changed During Deployment

| Change | Reason |
|---|---|
| ChromaDB → pgvector | ChromaDB stores data on local disk; Cloud Run containers lose all disk state on restart. pgvector lives in Cloud SQL which persists forever. |
| Redis removed | Redis was only used in the health check ping — it wasn't caching or queuing anything. Removed to simplify the stack. |
| Web search moved to `rag_fetch` node | Previously blocked idea generation by running sequentially before it. Now runs in parallel with RAG retrieval, cutting ~5s off each workflow run. |
| DuckDuckGo timeout 15s → 5s | GCP IPs are sometimes rate-limited by DuckDuckGo. A 5s timeout prevents blocking the workflow. |
| Backend `min-instances=1` | Eliminates cold start delay (~8s) on the first request after the container idles. |
| CORS from hardcoded localhost → env var | The `allowed_origins` setting is stored in Secret Manager; the backend reads it at startup and allows the frontend Cloud Run URL. |
