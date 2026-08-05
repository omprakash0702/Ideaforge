# IdeaForge - LangGraph Workflow Design

# 1. Overview

LangGraph is responsible for orchestrating the entire IdeaForge workflow.

Responsibilities:

* Manage workflow state
* Execute agents
* Control transitions
* Handle failures
* Track idea evolution

The workflow follows a state-machine architecture.

---

# 2. High-Level Workflow

```text
User Input
      │
      ▼
Generate Ideas
      │
      ▼
User Review Gate
      │
      ▼
Judge Ideas
      │
      ▼
Evolve Ideas
      │
      ▼
Tournament
      │
      ▼
Generate Report
      │
      ▼
End
```

---

# 3. State Object

The state object is shared across all nodes.

```python
class IdeaForgeState(TypedDict):

    project_id: str

    problem_statement: str

    generated_ideas: list

    evaluations: list

    evolved_ideas: list

    tournament_results: list

    winning_idea: dict

    final_report: str

    current_stage: str

    errors: list
```

---

# 4. Graph Nodes

## Node 1

Input Node

Purpose:

Receive user problem statement.

Output:

```json
{
  "problem_statement": ""
}
```

---

## Node 2

Generator Node

Purpose:

Run all generator agents.

Agents:

* Creative Founder
* Market Founder
* Builder Founder

Output:

```json
{
  "generated_ideas": []
}
```

Expected Output:

6 ideas

---

## Node 3

User Review Node

Purpose:

Allow user to:

* Continue
* Regenerate
* Remove ideas

Decision Point:

Human-in-the-loop validation.

---

## Node 4

Judge Node

Purpose:

Evaluate all generated ideas.

Agents:

* Investor Judge
* Engineer Judge
* Skeptic Judge

Output:

```json
{
  "evaluations": []
}
```

---

## Node 5

Evolution Node

Purpose:

Improve weak ideas.

Input:

Ideas + Judge Feedback

Output:

Improved Ideas

---

## Node 6

Tournament Node

Purpose:

Select strongest idea.

Input:

Ideas + Scores

Output:

Winner

---

## Node 7

Report Node

Purpose:

Generate final report.

Output:

Markdown report.

---

## Node 8

End Node

Purpose:

Return final response.

---

# 5. Graph Edges

```text
Input

↓

Generator

↓

User Review

↓

Judge

↓

Evolution

↓

Tournament

↓

Report

↓

End
```

---

# 6. Conditional Routing

## Route 1

After User Review

```text
Continue
     ↓
Judge Node
```

---

## Route 2

After User Review

```text
Regenerate
     ↓
Generator Node
```

---

## Route 3

After User Review

```text
Ideas Removed
     ↓
Judge Node
```

---

## Route 4

After Evolution

If:

```text
Score > 85
```

Skip additional evolution.

Proceed:

```text
Tournament
```

---

# 7. Parallel Execution

Generator Agents run in parallel.

```text
Creative Founder
Market Founder
Builder Founder
```

All outputs merged.

---

Judge Agents run in parallel.

```text
Investor Judge
Engineer Judge
Skeptic Judge
```

All evaluations merged.

---

Benefits:

* Faster execution
* Independent evaluation

---

# 8. Scoring Flow

For each idea:

```text
Investor Score

Engineer Score

Skeptic Score
```

↓

Average

↓

Final Score

Example:

```text
Investor = 8

Engineer = 7

Skeptic = 9

Average = 8

Final Score = 80
```

---

# 9. Evolution Logic

Input:

```text
Idea
+
Judge Feedback
```

Output:

```text
Improved Idea
```

Stop Conditions:

* Score > 85
* Improvement < 5 points
* Maximum 3 iterations

---

# 10. Tournament Flow

Input:

6 ideas

Round 1

```text
Top 2 scores
     ↓
Automatic Advance
```

Remaining:

```text
4 Ideas
```

↓

```text
4 → 2
```

↓

Final Four

↓

```text
4 → 2
```

↓

Final

```text
2 → 1
```

Winner Selected

---

# 11. Failure Handling

## Generator Failure

Retry once.

If failed:

Continue with remaining generators.

---

## Judge Failure

Retry once.

If failed:

Mark evaluation unavailable.

---

## Evolution Failure

Use previous version.

Continue workflow.

---

## Tournament Failure

Use latest valid scores.

Continue.

---

## Report Failure

Return partial report.

---

# 12. Execution Timeline

Expected Order:

```text
Input

↓

Generate

↓

Review

↓

Judge

↓

Evolve

↓

Tournament

↓

Report

↓

Complete
```

---

# 13. Future Nodes (Phase 2)

Not included in MVP.

Possible additions:

* Market Research Node
* Competitor Analysis Node
* Future Simulation Node
* Sarvam Translation Node
* Investor Persona Node

These can be attached without redesigning the graph.
