# IdeaForge - Data Model Design

# 1. Overview

IdeaForge uses two databases:

## PostgreSQL

Stores:

* Users
* Projects
* Ideas
* Evaluations
* Reports

## Neo4j

Stores:

* Idea Evolution Graph
* Idea Relationships
* Judge Relationships
* Version History

---

# 2. PostgreSQL Data Model

## Users Table

Purpose:

Store user information.

| Column     | Type      |
| ---------- | --------- |
| id         | UUID      |
| name       | VARCHAR   |
| email      | VARCHAR   |
| created_at | TIMESTAMP |

---

## Projects Table

Purpose:

Each user submission becomes a project.

| Column            | Type      |
| ----------------- | --------- |
| id                | UUID      |
| user_id           | UUID      |
| title             | VARCHAR   |
| problem_statement | TEXT      |
| status            | VARCHAR   |
| created_at        | TIMESTAMP |

Status:

```text
CREATED
GENERATING
JUDGING
EVOLVING
TOURNAMENT
COMPLETED
FAILED
```

---

## Ideas Table

Purpose:

Store all generated ideas.

| Column          | Type      |
| --------------- | --------- |
| id              | UUID      |
| project_id      | UUID      |
| version         | INTEGER   |
| title           | VARCHAR   |
| problem         | TEXT      |
| solution        | TEXT      |
| target_audience | TEXT      |
| business_model  | TEXT      |
| tech_stack      | TEXT      |
| score           | FLOAT     |
| is_winner       | BOOLEAN   |
| created_at      | TIMESTAMP |

---

## Evaluations Table

Purpose:

Store judge feedback.

| Column          | Type      |
| --------------- | --------- |
| id              | UUID      |
| idea_id         | UUID      |
| judge_type      | VARCHAR   |
| score           | FLOAT     |
| strengths       | JSONB     |
| weaknesses      | JSONB     |
| recommendations | JSONB     |
| created_at      | TIMESTAMP |

Judge Types:

```text
INVESTOR
ENGINEER
SKEPTIC
```

---

## Reports Table

Purpose:

Store final report.

| Column          | Type      |
| --------------- | --------- |
| id              | UUID      |
| project_id      | UUID      |
| winner_idea_id  | UUID      |
| markdown_report | TEXT      |
| created_at      | TIMESTAMP |

---

# 3. Database Relationships

```text
User
 │
 └── Projects
         │
         └── Ideas
                 │
                 └── Evaluations

Project
 │
 └── Report
```

---

# 4. Neo4j Data Model

Purpose:

Track idea evolution.

---

# 5. Nodes

## Idea Node

Properties:

```json
{
  "idea_id": "",
  "title": "",
  "score": 0,
  "version": 1
}
```

---

## Feature Node

Properties:

```json
{
  "name": ""
}
```

---

## Risk Node

Properties:

```json
{
  "name": ""
}
```

---

## Judge Node

Properties:

```json
{
  "name": "",
  "type": ""
}
```

---

## Project Node

Properties:

```json
{
  "project_id": "",
  "title": ""
}
```

---

# 6. Relationships

## Idea Evolution

```text
(Idea_V2)
    │
EVOLVED_FROM
    │
(Idea_V1)
```

---

## Feature Relationship

```text
(Idea)

HAS_FEATURE

(Feature)
```

---

## Risk Relationship

```text
(Idea)

HAS_RISK

(Risk)
```

---

## Judge Relationship

```text
(Idea)

CRITICIZED_BY

(Judge)
```

---

## Project Relationship

```text
(Project)

CONTAINS

(Idea)
```

---

# 7. Example Evolution Graph

```text
AI Tutor

      │
EVOLVED_FROM

      ▼

AI Tutor for JEE

      │
EVOLVED_FROM

      ▼

AI Tutor for Rural JEE Aspirants
```

This becomes visible in Neo4j visualization.

---

# 8. Versioning Strategy

Initial Idea:

```text
Version 1
```

After Evolution:

```text
Version 2
```

After Further Evolution:

```text
Version 3
```

Maximum:

```text
Version 4
```

(Original + 3 Evolutions)

---

# 9. Data Lifecycle

Step 1

Project created.

↓

Step 2

Ideas generated.

↓

Step 3

Ideas evaluated.

↓

Step 4

Ideas evolved.

↓

Step 5

Tournament selects winner.

↓

Step 6

Final report generated.

↓

Step 7

Project archived.

---

# 10. Future Extensions

Phase 2 tables:

## Market Research

```text
market_reports
```

## Competitor Analysis

```text
competitors
```

## Simulations

```text
simulation_results
```

## Multilingual Support

```text
translations
```

Not required for MVP.
