# IdeaForge - Agent Design

# 1. Overview

IdeaForge uses multiple specialized AI agents.

Each agent has a single responsibility and communicates through structured JSON outputs.

The goal is to avoid generic AI responses and create a multi-perspective evaluation system.

---

# 2. Agent Architecture

```text
User Input
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
Report Agent
```

---

# 3. Shared Idea Schema

All agents must use this structure.

```json
{
  "title": "",
  "problem": "",
  "solution": "",
  "target_audience": "",
  "business_model": "",
  "tech_stack": "",
  "key_features": []
}
```

---

# 4. Generator Agents

## Generator Agent 1

### Name

Creative Founder

### Purpose

Generate unconventional startup ideas.

### Focus

* Novelty
* Differentiation
* Unique approaches

### Input

Problem Statement

### Output

Idea Schema

### Success Criteria

Idea should be significantly different from common solutions.

---

## Generator Agent 2

### Name

Market Founder

### Purpose

Generate commercially viable ideas.

### Focus

* Revenue
* Market demand
* Monetization

### Input

Problem Statement

### Output

Idea Schema

### Success Criteria

Idea must have a clear business model.

---

## Generator Agent 3

### Name

Builder Founder

### Purpose

Generate buildable ideas.

### Focus

* MVP simplicity
* Technical feasibility
* Hackathon readiness

### Input

Problem Statement

### Output

Idea Schema

### Success Criteria

Idea should be achievable within a short development cycle.

---

# 5. Judge Agents

## Judge Agent 1

### Name

Investor Judge

### Purpose

Evaluate business viability.

### Evaluation Areas

* Market Size
* Revenue Potential
* Competitive Advantage

### Output

```json
{
  "judge": "Investor",
  "score": 0,
  "strengths": [],
  "weaknesses": [],
  "recommendations": []
}
```

---

## Judge Agent 2

### Name

Engineer Judge

### Purpose

Evaluate technical feasibility.

### Evaluation Areas

* Complexity
* Scalability
* Development Effort

### Output

```json
{
  "judge": "Engineer",
  "score": 0,
  "strengths": [],
  "weaknesses": [],
  "recommendations": []
}
```

---

## Judge Agent 3

### Name

Skeptic Judge

### Purpose

Challenge assumptions.

### Evaluation Areas

* Risks
* Hidden assumptions
* Failure modes

### Output

```json
{
  "judge": "Skeptic",
  "score": 0,
  "strengths": [],
  "weaknesses": [],
  "recommendations": []
}
```

---

# 6. Evolution Agent

## Purpose

Improve ideas using judge feedback.

---

## Input

Idea

*

Judge Feedback

---

## Output

Improved Idea

---

## Responsibilities

* Address weaknesses
* Reduce risks
* Improve feasibility
* Improve differentiation

---

## Success Criteria

Improved idea must solve at least one identified weakness.

---

# 7. Tournament Agent

## Purpose

Compare ideas and select winners.

---

## Inputs

Ideas

Scores

Judge Feedback

---

## Evaluation Criteria

* Market Potential
* Feasibility
* Novelty
* Monetization
* Hackathon Potential

---

## Output

Winning Idea

Reasoning

Final Score

---

# 8. Report Agent

## Purpose

Generate final user-facing report.

---

## Input

Winning Idea

Judge Feedback

Tournament Results

---

## Output

Markdown Report

Sections:

* Winning Idea
* Why It Won
* Risks
* Recommendations
* MVP Scope
* Execution Roadmap

---

# 9. Agent Communication Rules

All agents:

* Receive structured JSON
* Return structured JSON
* Never return plain text only
* Must provide reasoning for decisions

This ensures consistency across the workflow.

---

# 10. Future Agents (Phase 2)

Not part of MVP.

Potential additions:

* Market Research Agent
* Competitor Analysis Agent
* Future Simulation Agent
* Multilingual Agent
* Investor Persona Agent

```
```
