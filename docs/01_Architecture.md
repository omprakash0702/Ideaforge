# IdeaForge - System Architecture

# 1. System Overview

IdeaForge is an AI-powered Startup Survival Simulator.

The system accepts a startup problem statement, generates multiple startup ideas, evaluates them using specialized AI judges, evolves weak ideas, conducts tournament-style comparisons, and produces a final winning idea with an execution roadmap.

---

# 2. High-Level Architecture

```text
User
  │
  ▼
Frontend (Next.js)
  │
  ▼
FastAPI Backend
  │
  ▼
LangGraph Workflow Engine
  │
  ├── Generator Agents
  │
  ├── Judge Agents
  │
  ├── Evolution Agent
  │
  ├── Tournament Engine
  │
  └── Report Generator
  │
  ▼
Databases
(PostgreSQL + Neo4j)
```

---

# 3. Core Components

## Frontend

Responsibilities:

* User Input
* Idea Visualization
* Judge Feedback Display
* Tournament Dashboard
* Final Report Display

Technology:

* Next.js
* TailwindCSS
* Shadcn UI

---

## Backend

Responsibilities:

* API Layer
* Agent Orchestration
* Business Logic
* Data Persistence

Technology:

* FastAPI
* Pydantic

---

## LangGraph Workflow

Responsibilities:

* Manage agent execution
* Maintain workflow state
* Control transitions between stages

Technology:

* LangGraph

---

## Database Layer

Responsibilities:

* Store projects
* Store ideas
* Store evaluations
* Store reports
* Store idea evolution graph

Technologies:

* PostgreSQL
* Neo4j

---

# 4. Functional Components

## Component 1

Generator Layer

Purpose:

Generate candidate startup ideas.

Output:

Multiple structured ideas.

---

## Component 2

Judge Layer

Purpose:

Evaluate generated ideas.

Output:

Scores

Strengths

Weaknesses

Recommendations

---

## Component 3

Evolution Layer

Purpose:

Improve weak ideas using judge feedback.

Output:

Improved versions of ideas.

---

## Component 4

Tournament Engine

Purpose:

Compare competing ideas and eliminate weaker ones.

Output:

Winning idea.

---

## Component 5

Report Generator

Purpose:

Generate final execution-ready report.

Output:

Markdown report.

---

# 5. Workflow Architecture

```text
Problem Statement
        │
        ▼
Generator Agents
        │
        ▼
Generated Ideas
        │
        ▼
Judge Agents
        │
        ▼
Evaluations
        │
        ▼
Evolution Agent
        │
        ▼
Improved Ideas
        │
        ▼
Tournament Engine
        │
        ▼
Winning Idea
        │
        ▼
Report Generator
        │
        ▼
Final Report
```

---

# 6. LangGraph State

The workflow maintains a shared state.

State contains:

* Project Information
* User Input
* Generated Ideas
* Judge Feedback
* Evolved Ideas
* Scores
* Tournament Results
* Final Report

---

# 7. Data Flow

Step 1

User submits startup problem.

↓

Step 2

Generator agents create ideas.

↓

Step 3

Ideas are stored.

↓

Step 4

Judge agents evaluate ideas.

↓

Step 5

Evaluations are stored.

↓

Step 6

Evolution agent improves ideas.

↓

Step 7

Tournament engine selects winner.

↓

Step 8

Report generator creates final report.

↓

Step 9

Results returned to user.

---

# 8. Database Architecture

## PostgreSQL

Stores:

* Users
* Projects
* Ideas
* Evaluations
* Reports

---

## Neo4j

Stores:

* Idea Evolution Graph
* Idea Relationships
* Version History

Example:

Idea V1

↓

Idea V2

↓

Idea V3

---

# 9. Failure Handling

Generator Failure

↓

Retry once

↓

If failed, continue with remaining generators

---

Judge Failure

↓

Retry once

↓

Mark evaluation unavailable

---

Evolution Failure

↓

Use previous version

---

Report Failure

↓

Return partial report

---

# 10. Deployment Architecture

| Component | Platform |
|---|---|
| Frontend (Next.js) | GCP Cloud Run |
| Backend (FastAPI) | GCP Cloud Run |
| PostgreSQL + pgvector | GCP Cloud SQL (PostgreSQL 15) |
| Neo4j | GCP GCE e2-micro — Neo4j Community Edition |

CI/CD: Cloud Build trigger on push to `main` → Docker build → Artifact Registry → Cloud Run deploy.

---

# 11. Scalability Considerations

Future enhancements:

* Market research agents
* Sarvam multilingual support (Phase 2 — limited credits, not in MVP)
* Simulation engine
