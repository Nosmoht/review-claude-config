---
name: review-agent
description: >
  Evaluate a single Claude Code agent (.md file) across 7 dimensions with
  agent-specific checks: model selection appropriateness, description/example
  block activation precision, and trigger pattern coverage. Produces a quality
  certificate with concrete optimization recommendations. Use when reviewing
  an individual agent or when delegated by /review-claude-config.
argument-hint: <path-to-agent.md>
allowed-tools: Read, Write, Glob, WebSearch, WebFetch
---

# Review Agent

Evaluate a single Claude Code agent for quality across 7 evidence-based dimensions with agent-specific checks.

## Argument Handling

- `$ARGUMENTS` is the path to an agent .md file.
- Validate the file exists. Agents are single-file, typically in `.claude/agents/` or an `agents/` directory, with optional frontmatter containing `model`, `tools`, or `description`.
- If the file does not look like an agent (e.g., it's a SKILL.md or rule), report the error and stop.

## Mode Detection

Check whether the prompt contains an orchestration metadata block:

```
---orchestration---
mode: orchestrated
websearch_available: true|false
webfetch_available: true|false
domain_cache: |
  <cached domain content or "none">
---
```

- If present → **orchestrated mode** (skip tool checks, use provided flags and cache, return structured certificate only, no user interaction).
- If absent → **standalone mode** (full workflow below).

## Phase 1 — Setup (standalone mode only)

### Step 0: Tool Availability Checks

Attempt a trivial WebSearch (e.g., "Claude Code documentation"). If it fails, set `websearch_available = false`. Goal Alignment will be scored from model knowledge only, marked `[no web verification]`.

Attempt a trivial WebFetch (e.g., fetch "https://docs.anthropic.com"). If it fails, set `webfetch_available = false`.

### Step 1: Load References

Locate the `review-claude-config` skill directory (sibling skill in the same plugin). Read these shared references from it:
- `references/scoring-rubric.md` — the grading criteria
- `references/engineering-baseline.md` — prompt, context, and tool design techniques

Use Glob to find the files if the path is not immediately known: `**/review-claude-config/references/scoring-rubric.md`

**If either file is not found, abort with error:** "Required reference not found. Ensure review-claude-config is installed as a sibling skill."

Read the type-specific evaluation guide from this skill's own directory:
- `references/agent-evaluation-guide.md`

## Phase 2 — Evaluation

### Step A: Goal Inference + Domain Research

1. Read the agent file and infer its primary goal/domain in one sentence.
2. Domain research (follow orchestration flags if in orchestrated mode):
   - If `websearch_available`: perform 1-2 WebSearch queries for domain best practices.
   - If `webfetch_available`: fetch 1-2 most relevant URLs with WebFetch using prompt: "Extract domain best practices, benchmarks, and configuration patterns relevant to [domain]. Max 500 words."
   - If neither available: use model knowledge only.
3. Synthesize: what should a high-quality agent in this domain include?

### Step B: Scoring + Recommendations

Score using the rubric as the PRIMARY basis. The agent evaluation guide provides type-specific criteria. Domain research informs Goal Alignment and enriches recommendations but does NOT alter scoring criteria for other dimensions.

**Agent-specific evaluation criteria** (from evaluation guide):
- **Clarity**: Check that instructions are unambiguous within the single-file constraint. Section structure for longer agents.
- **Completeness**: Check `<example>` blocks for trigger pattern coverage. If no examples and description is ambiguous → C or below.
- **Prompt Engineering**: Check for role priming, structured output, constraints, few-shot via `<example>` blocks.
- **Context Engineering**: Evaluate description and example blocks for **activation precision**, not progressive disclosure (agents are single-file). If description is generic enough to match unrelated requests → C or below.
- **Goal Alignment**: Check domain knowledge, tool/structure fit. Does the agent body support achieving the goal described in the description?
- **Safety**: Check least-privilege tools, guardrails for destructive actions if Write/Bash/Edit are available.
- **Metadata**: Check `model` field appropriateness (haiku/sonnet/opus vs task complexity). Check `tools`/`allowed-tools` matches actual usage. Check description accuracy.

## Phase 3 — Output

Return the report in this EXACT format:

### Goal
[One sentence describing what this agent aims to achieve]

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | [A-F] | 15% | [One line] |
| Completeness | [A-F] | 15% | [One line] |
| Prompt Engineering | [A-F] | 15% | [One line] |
| Context Engineering | [A-F] | 15% | [One line] |
| Goal Alignment | [A-F] | 20% | [One line] |
| Safety | [A-F] | [10/15%] | [One line] |
| Metadata | [A-F] | [10/5%] | [One line] |
| **Overall** | **[A-F]** | **100%** | **Weighted: XX.X** |

Calculate overall grade:
1. Determine weights: if agent has Write/Bash/Edit in tools/allowed-tools, Safety=15% and Metadata=5%; otherwise Safety=10% and Metadata=10%. All other weights unchanged.
2. Convert grades: A=95, B=85, C=75, D=65, F=50.
3. Weighted score = sum(grade_value × weight) for all 7 dimensions.
4. Map back: ≥90→A, ≥80→B, ≥70→C, ≥60→D, <60→F.
5. Show in Overall Justification: "Weighted: XX.X → [Grade]"

### Grading Boundary Examples

**Clarity B vs C:** B has a clear workflow where step order is unambiguous but one conditional ("if needed") lacks specific criteria. C has steps that two models would sequence differently because dependencies between steps are not explicit.

**Safety B vs C:** B restricts tools to what's needed and includes a confirmation gate before writes. C has tools broader than needed (e.g., Bash when only Read is required) or could modify user files without explicit confirmation.

[If WebSearch was unavailable, add: "Goal Alignment scored without web verification."]

### Strengths
- [strength 1]
- [strength 2]
- [strength 3 if applicable]

### Recommendations

#### 1. [Title] (Impact: [High/Medium/Low])
[What to change and why, referencing baseline techniques or domain best practices]

**Current:**
```
[existing text from the agent]
```

**Recommended:**
```
[improved text — concrete rewrite]
```

[Repeat for each recommendation, ordered by impact]

#### Reference File Recommendation
[Note: Agents are single-file and cannot have reference files. If the agent would benefit from extracted reference content, recommend converting to a skill instead, explaining the tradeoff.]

## Phase 4 — Report Persistence (standalone mode only)

In orchestrated mode, skip this phase entirely — return only the structured certificate above.

In standalone mode:
1. Present the certificate to the user.
2. Confirm before writing: "Save review report to `<target>/.claude/reviews/YYYY-MM-DDTHHMMSS-review-agent.md`?"
3. If confirmed, assemble report with YAML frontmatter:

```yaml
---
generated_by: review-agent
schema_version: 1
date: YYYY-MM-DD
target: /absolute/path/to/agent
baseline_version: YYYY-MM-DD
items_reviewed: 1
summary:
  - name: agent-name
    type: Agent
    path: relative/path/to/agent.md
    overall: B
    score: 85.0
    clarity: B
    completeness: A
    prompt_engineering: B
    context_engineering: B
    goal_alignment: B
    safety: A
    metadata: B
---
```

4. Write the report file. Suggest committing with: `docs(reviews): add YYYY-MM-DDTHHMMSS review report`

## Error Handling

On evaluation failure, return a structured error block:

```
## ERROR
{item_path}: {reason}
```

In orchestrated mode, the orchestrator logs this and continues with remaining items.

## Hard Rules

- **Read-only on the analyzed agent.** Never modify the agent being reviewed. Write only to `.claude/reviews/`.
- **Apply the rubric strictly.** Do not inflate grades.
- **Every recommendation must include a concrete rewrite** — not just "improve X."
- **Present the full certificate before any follow-up actions.**
