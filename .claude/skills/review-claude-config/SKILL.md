---
name: review-claude-config
description: >
  Analyze and optimize all Claude Code skills and agents in a project's .claude/
  directory. Applies evidence-based prompt and context engineering evaluation,
  produces per-item quality certificates with concrete optimization
  recommendations. Use when you want to audit skill/agent quality or before
  shipping new skills.
argument-hint: [folder]
allowed-tools: Agent, Read, Glob, Grep, WebSearch
---

# Review Claude Config

Analyze all Claude Code skills and agents in a target folder and produce per-item quality certificates with optimization recommendations.

## Argument Handling

- `$ARGUMENTS` is the target folder path. If empty, use the current working directory.
- Validate the folder exists. If no `.claude/` directory is found at any level, report that and stop.

## Phase 1 — Setup and Discovery

### Step 0: WebSearch Availability Check

Attempt a trivial WebSearch (e.g., "Claude Code documentation"). If it fails or is unavailable, set `websearch_available = false` and continue. Goal Alignment will be scored from model knowledge only, marked `[no web verification]` on the certificate.

### Steps 1-2: Launch in parallel

**1. Load References**

Read these files from the skill's own `references/` directory:
- `references/scoring-rubric.md` — the grading criteria
- `references/engineering-baseline.md` — prompt, context, and tool design techniques

Check `last_refreshed` date in the baseline frontmatter. If older than 3 months, warn the user: "Baseline was last refreshed on [date]. Consider running `/refresh-engineering-baseline` for current best practices."

**2. Discovery Agent**

Launch an Agent to discover all skills and agents in the target folder:

```
Discover all Claude Code skills and agents. Use Glob with these patterns:
- <folder>/.claude/skills/*/SKILL.md
- <folder>/.claude/agents/*.md
- <folder>/**/.claude/skills/*/SKILL.md (monorepo support)
- <folder>/**/.claude/agents/*.md (monorepo support)

Exclude paths containing: node_modules, .git, vendor, dist, build

For each discovered file:
- Read the full content
- Classify as "Skill" or "Agent"
- Return: file path, type, full content

Also note (but do not analyze): existence of CLAUDE.md, .claude/rules/, .claude/settings.json
```

If no skills or agents are discovered, report that and stop.

## Phase 2 — Per-Item Analysis

For each discovered item, launch an analysis Agent. Process in parallel, batched in groups of 8 (if more than 8 items). Present each batch's results before starting the next. Partial final batches are handled identically.

Each analysis agent receives a **byte-identical shared prefix** (rubric + baseline content) followed by per-item specifics. This preserves KV-cache hits across agents.

### Analysis Agent Prompt Template

```
You are evaluating a Claude Code [Skill/Agent] for quality.

## Reference Materials

### Scoring Rubric
[Insert scoring-rubric.md content here]

### Engineering Baseline
[Insert engineering-baseline.md content here]

## Item Under Review

**Type:** [Skill/Agent]
**Path:** [file path]
**Content:**
[Insert full file content here]

## Your Task — Two Steps

### Step A: Goal Inference + Domain Research

1. Read the item and infer its primary goal/domain in one sentence.
2. [If WebSearch available] Search for domain-specific best practices relevant to
   this goal. Use 1-2 targeted queries (e.g., "[domain] best practices",
   "[domain] automation checklist"). Extract only actionable best practices —
   do not dump raw search results.
3. Synthesize: what should a high-quality item in this domain include?

### Step B: Scoring + Recommendations

Score using the rubric as the PRIMARY basis. Domain research from Step A informs
Goal Alignment and enriches recommendations but does NOT alter scoring criteria
for other dimensions.

Return your report in this EXACT format:

### Goal
[One sentence describing what this item aims to achieve]

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
| **Overall** | **[A-F]** | **100%** | |

[If WebSearch was unavailable, add: "Goal Alignment scored without web
verification."]

### Strengths
- [strength 1]
- [strength 2]
- [strength 3 if applicable]

### Recommendations

#### 1. [Title] (Impact: [High/Medium/Low])
[What to change and why, referencing baseline techniques or domain best practices]

**Current:**
```
[existing text from the item]
```

**Recommended:**
```
[improved text — concrete rewrite]
```

[Repeat for each recommendation, ordered by impact]

#### Reference File Recommendation
[If applicable: flag whether bundled reference files (checklists, rubrics, domain
guides in a references/ subdirectory) would improve this item's context
engineering. Explain what to extract and why.]
```

## Phase 3 — Presentation

Present each item's report to the user. After all items, add:

### Summary Table

```
## Summary

| Item | Type | Overall | Clarity | Completeness | PE | CE | Goal | Safety | Meta |
|------|------|---------|---------|--------------|----|----|------|--------|------|
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
```

### Cross-Cutting Observations

Identify patterns across items:
- Common anti-patterns (e.g., consistent tool bloat, missing output formats)
- Consistent strengths (e.g., good safety practices across all items)
- Systemic recommendations (e.g., "all agents would benefit from reference files")
- Missing CLAUDE.md guidance that would benefit all items

## Hard Rules

- **Read-only.** Never modify any files. Baseline is maintained via `/refresh-engineering-baseline`.
- **Analyze every discovered item.** Skip none.
- **Apply the rubric strictly.** Do not inflate grades.
- **Every recommendation must include a concrete rewrite** — not just "improve X."
- **Present all reports before asking** about follow-up actions.
- **Error handling:** If an analysis agent fails, report the failure with partial results and continue with remaining items. Never silently skip.
