# IdeaForge - Implementation Plan

## Goal

Build IdeaForge incrementally, ensuring every milestone results in a working, testable system.

---

# Milestone 1 - Project Foundation

## Objective

Set up the project structure and development environment.

### Tasks

* Create repository structure
* Configure FastAPI
* Configure Next.js
* Configure PostgreSQL connection
* Configure Neo4j connection
* Configure environment variables
* Configure logging
* Configure dependency injection
* Configure Docker (optional)
* Create health check endpoint

### Deliverables

* Backend runs successfully
* Frontend runs successfully
* Database connections established

---

# Milestone 2 - Database Layer

## Objective

Implement persistence layer.

### Tasks

* SQLAlchemy models
* Alembic migrations
* Repository pattern
* Database sessions
* CRUD operations

Tables

* Users
* Projects
* Ideas
* Evaluations
* Reports

Neo4j

* Connection
* Nodes
* Relationships

### Deliverables

* Database initialized
* CRUD tested

---

# Milestone 3 - LangGraph Foundation

## Objective

Build workflow engine.

### Tasks

* Create State object
* Register nodes
* Register edges
* Conditional routing
* Workflow execution

### Deliverables

* Graph executes dummy nodes
* State transitions verified

---

# Milestone 4 - Generator Layer

## Objective

Generate startup ideas.

### Tasks

* BaseAgent class
* Creative Founder
* Market Founder
* Builder Founder
* JSON validation
* Retry logic

### Deliverables

* Six startup ideas generated
* Structured JSON output

---

# Milestone 5 - Judge Layer

## Objective

Evaluate ideas.

### Tasks

* Investor Judge
* Engineer Judge
* Skeptic Judge
* Scoring logic
* Feedback generation

### Deliverables

* Every idea evaluated
* Structured feedback produced

---

# Milestone 6 - Evolution Engine

## Objective

Improve weak ideas.

### Tasks

* Read judge feedback
* Generate improved ideas
* Version tracking
* Stop conditions

### Deliverables

* Improved idea versions
* Version history maintained

---

# Milestone 7 - Tournament Engine

## Objective

Select the strongest idea.

### Tasks

* Ranking algorithm
* Elimination rounds
* Winner selection
* Score aggregation

### Deliverables

* One winning idea selected

---

# Milestone 8 - Report Generator

## Objective

Generate final report.

### Tasks

* Winner summary
* Judge feedback
* Risk analysis
* MVP recommendation
* Tech stack recommendation
* Execution roadmap

### Deliverables

* Markdown report generated

---

# Milestone 9 - FastAPI Integration

## Objective

Expose backend functionality.

### Tasks

* Create REST APIs
* Validation
* Exception handling
* Connect services
* Response models

### Deliverables

* End-to-end backend pipeline

---

# Milestone 10 - Frontend

## Objective

Build user interface.

### Pages

* Landing
* Dashboard
* Idea Cards
* Judge Dashboard
* Tournament View
* Final Report

### Deliverables

* Functional frontend
* Backend integration

---

# Milestone 11 - Neo4j Visualization

## Objective

Visualize idea evolution.

### Tasks

* Store evolution graph
* Display relationships
* Display version history

### Deliverables

* Interactive graph visualization

---

# Milestone 12 - Testing

## Objective

Validate system behavior.

### Tests

* Unit Tests
* API Tests
* Workflow Tests
* Integration Tests

### Deliverables

* Stable MVP

---

# Milestone 13 - Deployment

## Objective

Deploy application.

### Platform

| Component | Platform |
|---|---|
| Frontend | GCP Cloud Run |
| Backend | GCP Cloud Run |
| PostgreSQL + pgvector | GCP Cloud SQL |
| Neo4j | GCP GCE e2-micro (Neo4j Community — free) |

CI/CD via Cloud Build trigger on push to `main`.

### Deliverables

* Live application on Cloud Run
* Cloud Build trigger wired to GitHub repo
* Secrets in GCP Secret Manager

---

# Development Workflow

For every milestone:

1. Update architecture if needed.
2. Ask Claude to generate only that milestone.
3. Review the generated code.
4. Run locally.
5. Fix issues.
6. Commit to Git.
7. Move to the next milestone.

---

# Git Commit Strategy

After each milestone:

```text
feat: project foundation

feat: database layer

feat: langgraph workflow

feat: generator agents

feat: judge agents

feat: evolution engine

feat: tournament engine

feat: report generator

feat: api integration

feat: frontend dashboard

feat: neo4j visualization

chore: deployment
```

---

# Definition of Done (MVP)

A user should be able to:

1. Enter a startup problem.
2. Generate multiple ideas.
3. Review generated ideas.
4. Receive evaluations from multiple judges.
5. View evolved ideas.
6. Watch tournament elimination.
7. Receive one winning idea.
8. Download a structured markdown report.
9. Complete the entire pipeline in a single session.
