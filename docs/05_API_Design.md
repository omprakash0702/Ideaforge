# IdeaForge - API Design

# 1. Overview

The FastAPI backend exposes APIs for:

* Project Creation
* Idea Generation
* Idea Evaluation
* Idea Evolution
* Tournament Execution
* Report Generation

All APIs communicate using JSON.

Base URL:

```text
/api/v1
```

---

# 2. API Flow

```text
Create Project

↓

Generate Ideas

↓

Judge Ideas

↓

Evolve Ideas

↓

Run Tournament

↓

Generate Report

↓

Get Results
```

---

# 3. Create Project

## Endpoint

```http
POST /projects
```

### Request

```json
{
  "title": "AI for Farmers",
  "problem_statement": "Help farmers improve crop yield"
}
```

### Response

```json
{
  "project_id": "uuid",
  "status": "CREATED"
}
```

---

# 4. Generate Ideas

## Endpoint

```http
POST /projects/{project_id}/generate
```

### Purpose

Run all generator agents.

### Response

```json
{
  "ideas": [
    {
      "idea_id": "uuid",
      "title": "Smart Crop Advisor"
    }
  ]
}
```

---

# 5. User Review

## Endpoint

```http
POST /projects/{project_id}/review
```

### Purpose

User decides:

* Continue
* Regenerate
* Remove Ideas

### Request

```json
{
  "action": "continue"
}
```

or

```json
{
  "action": "remove",
  "idea_ids": [
    "id1",
    "id2"
  ]
}
```

### Response

```json
{
  "status": "accepted"
}
```

---

# 6. Judge Ideas

## Endpoint

```http
POST /projects/{project_id}/judge
```

### Purpose

Run all judge agents.

### Response

```json
{
  "evaluations": [
    {
      "idea_id": "uuid",
      "judge": "Investor",
      "score": 8
    }
  ]
}
```

---

# 7. Evolve Ideas

## Endpoint

```http
POST /projects/{project_id}/evolve
```

### Purpose

Improve ideas using judge feedback.

### Response

```json
{
  "evolved_ideas": []
}
```

---

# 8. Run Tournament

## Endpoint

```http
POST /projects/{project_id}/tournament
```

### Purpose

Determine winner.

### Response

```json
{
  "winner_id": "uuid",
  "score": 88
}
```

---

# 9. Generate Report

## Endpoint

```http
POST /projects/{project_id}/report
```

### Purpose

Generate final report.

### Response

```json
{
  "report_id": "uuid"
}
```

---

# 10. Get Report

## Endpoint

```http
GET /projects/{project_id}/report
```

### Response

```json
{
  "report_id": "uuid",
  "winner": {},
  "report": "markdown"
}
```

---

# 11. Get Project Status

## Endpoint

```http
GET /projects/{project_id}/status
```

### Response

```json
{
  "project_id": "uuid",
  "status": "JUDGING"
}
```

Possible Status Values:

```text
CREATED
GENERATING
REVIEWING
JUDGING
EVOLVING
TOURNAMENT
REPORTING
COMPLETED
FAILED
```

---

# 12. Request Schemas

## CreateProjectRequest

```python
class CreateProjectRequest(BaseModel):
    title: str
    problem_statement: str
```

---

## ReviewRequest

```python
class ReviewRequest(BaseModel):
    action: str
    idea_ids: list[str] = []
```

---

# 13. Response Schemas

## ProjectResponse

```python
class ProjectResponse(BaseModel):
    project_id: str
    status: str
```

---

## StatusResponse

```python
class StatusResponse(BaseModel):
    project_id: str
    status: str
```

---

# 14. Error Handling

## Validation Error

HTTP:

```text
422
```

Response:

```json
{
  "detail": "Invalid request"
}
```

---

## Project Not Found

HTTP:

```text
404
```

Response:

```json
{
  "detail": "Project not found"
}
```

---

## Internal Error

HTTP:

```text
500
```

Response:

```json
{
  "detail": "Unexpected error"
}
```

---

# 15. Service Layer Design

FastAPI Route

↓

Service Layer

↓

LangGraph Workflow

↓

Database Layer

Architecture:

```text
API

↓

Services

↓

LangGraph

↓

Repositories

↓

Database
```

---

# 16. Future APIs (Phase 2)

Not included in MVP.

Potential APIs:

```http
POST /simulate

POST /market-research

POST /competitor-analysis

POST /translate
```

---

# 17. MVP Simplification

For MVP:

Preferred endpoint:

```http
POST /projects/{project_id}/run
```

This single endpoint executes:

```text
Generate
↓
Judge
↓
Evolve
↓
Tournament
↓
Report
```

and returns final results.

This reduces frontend complexity and is recommended for hackathon implementation.
