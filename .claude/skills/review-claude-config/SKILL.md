---
name: review-claude-config
description: >
  Analyze and optimize all Claude Code skills and agents in a project's .claude/
  directory. Applies evidence-based prompt and context engineering evaluation,
  produces per-item quality certificates with concrete optimization
  recommendations. Use when you want to audit skill/agent quality or before
  shipping new skills.
argument-hint: [folder]
allowed-tools: Agent, Read, Write, Glob, WebSearch
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

Launch an Agent (allowed-tools: Glob, Read) to discover all skills and agents in the target folder:

```
Discover all Claude Code skills and agents. Use Glob with these patterns:
- <folder>/.claude/skills/*/SKILL.md
- <folder>/.claude/agents/*.md
- <folder>/**/.claude/skills/*/SKILL.md (monorepo support)
- <folder>/**/.claude/agents/*.md (monorepo support)

Exclude paths containing: node_modules, .git, vendor, dist, build, .claude/reviews

For each discovered file:
- Read the full content
- Classify as "Skill" or "Agent"
- Return: file path, type, full content

Also note (but do not analyze): existence of CLAUDE.md, .claude/rules/, .claude/settings.json
```

If no skills or agents are discovered, report that and stop.

## Phase 2 — Per-Item Analysis

### Step 0: Domain Cache Lookup

Before dispatching analysis agents, the orchestrator performs domain cache lookup:

1. **Infer canonical domain keys.** For each discovered item, extract the primary technology/framework from the item's `description` frontmatter field and first ~200 tokens of content. Produce a lowercase hyphenated slug (e.g., `kubernetes`, `react-testing`, `terraform-iac`).
   - Prefer the specific technology name over generic categories (e.g., `argocd` not `gitops`; `pytest` not `python-testing`). If ambiguous, use the skill's directory name as tiebreaker.
   - Use compound keys when items target distinct sub-domains (e.g., `react-testing` and `react-performance` rather than collapsing both to `react`). Broader keys are preferred only when items genuinely overlap.
   - If no clear domain is inferable (e.g., a generic "code-review" or "commit" skill), skip cache lookup for that item and use current behavior (WebSearch or model knowledge).
   - **Normalization pass:** After inferring keys for all items, review the full list and normalize near-duplicates (e.g., collapse `react-test` and `react-testing` to the more specific form).

2. **Lookup cached research.** Read `references/domain-cache/INDEX.md`. For each unique domain key:
   - If found in index, check `last_refreshed` date: **CACHED** (<90 days) or **STALE** (≥90 days)
   - If not found: **MISS**
   - For CACHED/STALE: read the full `references/domain-cache/{domain-key}.md` on-demand. If index says CACHED but the file is missing, treat as MISS.
   - If INDEX.md is missing or fails to parse, treat all domains as MISS and log a warning.

3. **Assign one researcher per domain.** For STALE/MISS domains shared by multiple items, designate only **one** analysis agent as the "researcher" for that domain. Other agents sharing the same domain are told: "Another agent is researching this domain — use cached content or model knowledge, do not WebSearch for domain research."

### Step 1: Dispatch Analysis Agents

For each discovered item, launch an analysis Agent with allowed-tools: WebSearch, Read (no Write, Edit, or Bash). Process in parallel, batched in groups of 8 (if more than 8 items). Present each batch's results before starting the next. Partial final batches are handled identically.

Each analysis agent receives a **byte-identical shared prefix** (rubric + baseline content) followed by per-item specifics. This preserves KV-cache hits across agents.

### Analysis Agent Prompt Template

```
You are evaluating a Claude Code [Skill/Agent] for quality.

Tools available: WebSearch (for domain research) and Read. Do not use Write, Edit,
or Bash. You are evaluating, not modifying.

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

## Domain Research Cache

**Domain:** [domain key or "none"]
**Cache Status:** [CACHED | STALE | MISS | NONE]
**Role:** [researcher | consumer]

[If CACHED:]
The following domain best practices were previously researched and cached.
Use these as your domain knowledge for Step A — skip WebSearch for domain
research. If cached content is clearly insufficient for this specific item,
you may perform 1 supplemental WebSearch query.

[Insert cached content here]

[If STALE + researcher:]
The following domain research was cached but is older than 90 days. Use it
as a starting point, then perform 1 WebSearch query to verify and update.
Return updated findings in the Domain Cache Update section at the end.

[Insert cached content here]

[If STALE + consumer:]
The following domain research was cached (older than 90 days). Another agent
is refreshing this domain. Use cached content as-is for your analysis.

[Insert cached content here]

[If MISS + researcher:]
No cached domain research exists. Perform 1-2 WebSearch queries as normal.
Return your findings in the Domain Cache Update section at the end.

[If MISS + consumer:]
No cached domain research exists and another agent is researching this domain.
Use model knowledge only for domain context.

[If NONE:]
No domain was inferred for this item. Proceed with WebSearch as normal.

## Your Task — Two Steps

### Step A: Goal Inference + Domain Research

1. Read the item and infer its primary goal/domain in one sentence.
2. Follow the Domain Research Cache instructions above:
   - CACHED: use cached content, skip WebSearch (1 supplemental query if insufficient)
   - STALE researcher: use cache as starting point + 1 WebSearch to verify/update
   - STALE consumer: use cached content as-is
   - MISS researcher: 1-2 WebSearch queries (standard behavior)
   - MISS consumer: model knowledge only
   - NONE: 1-2 WebSearch queries (standard behavior)
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
| **Overall** | **[A-F]** | **100%** | **Weighted: XX.X** |

Calculate overall grade:
1. Determine weights: if item has Write/Bash/Edit in allowed-tools,
   Safety=15% and Metadata=5%; otherwise Safety=10% and Metadata=10%.
   All other weights unchanged (Clarity 15%, Completeness 15%, PE 15%,
   CE 15%, Goal Alignment 20%).
2. Convert grades: A=95, B=85, C=75, D=65, F=50.
3. Weighted score = sum(grade_value × weight) for all 7 dimensions.
4. Map back: ≥90→A, ≥80→B, ≥70→C, ≥60→D, <60→F.
5. Show in Overall Justification: "Weighted: XX.X → [Grade]"

Example (no Write/Bash/Edit): Clarity=A(95), Completeness=B(85), PE=B(85),
CE=A(95), Goal=B(85), Safety=A(95), Meta=B(85).
Score = 95×.15 + 85×.15 + 85×.15 + 95×.15 + 85×.20 + 95×.10 + 85×.10 = 89.0 → B

### Grading Boundary Examples

**Clarity B vs C:** B has a clear workflow where step order is unambiguous but one
conditional ("if needed") lacks specific criteria. C has steps that two models would
sequence differently because dependencies between steps are not explicit.

**Safety B vs C:** B restricts tools to what's needed and includes a confirmation gate
before writes. C has tools broader than needed (e.g., Bash when only Read is required)
or could modify user files without explicit confirmation.

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

### Domain Cache Update
[Only include if Role is "researcher" AND Cache Status is STALE or MISS.
Omit this section entirely for CACHED items and consumer-role agents.]

**Domain:** [domain key]
**Queries Used:**
- "[query 1]"
- "[query 2]"
**Sources:**
- [title](url)
**Best Practices:**
- [dense bullet 1]
- [dense bullet 2]
- [keep to ≤500 tokens total — no prose paragraphs]
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

## Phase 3.5 — Domain Cache Persistence

After presenting all reports, confirm before writing:
"Update domain cache with research for: [list of domain keys]?"

If the user declines, skip cache persistence.

1. Create the `references/domain-cache/` directory if it does not exist.
2. Collect all "Domain Cache Update" sections from researcher agents that had STALE or MISS cache status.
3. For each update, format as a cache entry file with YAML frontmatter and body (≤500 tokens of bullet content — truncate if exceeded):

```yaml
---
domain: [domain-key]
last_refreshed: [today's date YYYY-MM-DD]
queries:
  - "[query 1]"
  - "[query 2]"
sources:
  - url: [url]
    title: "[title]"
---

# [Domain Name] — Domain Best Practices

- [bullet 1]
- [bullet 2]
...
```

4. Write each entry to `references/domain-cache/{domain-key}.md`.
5. Update `references/domain-cache/INDEX.md` — add or update rows for each written domain key. Create INDEX.md if it does not exist.
6. If `websearch_available = false`, skip this entire phase — never write cache entries from model knowledge alone.
7. Report to user: "Updated domain cache: [list of domain keys written/updated]"

## Phase 4 — Report Persistence

After presenting all reports to the user, confirm before writing:
"Save review report to `<target>/.claude/reviews/YYYY-MM-DDTHHMMSS-review-claude-config.md`?"

If the user declines, skip report writing but still display the report path that would have been used.

### Step 1: Assemble report

Construct a Markdown file with YAML frontmatter and full body.

**Frontmatter:**
```yaml
---
generated_by: review-claude-config
schema_version: 1
date: YYYY-MM-DD
target: /absolute/path/to/target
baseline_version: YYYY-MM-DD
items_reviewed: N
summary:
  - name: item-name
    type: Skill
    path: relative/path/to/file
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

**Body:** All per-item reports (Goal + Certificate + Strengths + Recommendations), Summary Table, Cross-Cutting Observations.

**Large codebase handling:** If more than 20 items are reviewed, include full per-item reports only for items scoring C or below. A/B items get a one-line summary row only. All items are still analyzed and included in the Summary Table and frontmatter summary (preserves the "Analyze every discovered item" hard rule — analysis is not skipped, only report detail is reduced).

### Step 2: Write the report

Write to: `<target>/.claude/reviews/YYYY-MM-DDTHHMMSS-review-claude-config.md`

Use the current date and time for the timestamp. Create the `<target>/.claude/reviews/` directory if it does not exist. Timestamp ensures each run produces a unique file, supporting the "iterate until convergence" workflow.

### Step 3: Delta comparison

If a previous review report exists in `<target>/.claude/reviews/`:
- Read the most recent prior report's frontmatter `summary` block
- Compare each item's current grades against prior grades
- Append a "Delta from Prior Review" section to the report body:

```
## Delta from Prior Review ([prior report date])

| Item | Dimension | Previous | Current | Change |
|------|-----------|----------|---------|--------|
| [only rows where grades changed] |
```

If no prior report exists, skip this step.

### Step 4: Confirm

Tell the user the report file path and suggest committing with: `docs(reviews): add YYYY-MM-DDTHHMMSS review report` (using the timestamp from the report filename). This ensures the docs commit and subsequent fix commits (`fix(<scope>): address findings from YYYY-MM-DDTHHMMSS review`) share the same identifier for traceability.

## Hard Rules

- **Read-only on analyzed files.** Never modify any discovered skill, agent, or reference file. The only files this skill writes are the review report at `<target>/.claude/reviews/YYYY-MM-DDTHHMMSS-review-claude-config.md` and domain cache entries in its own `references/domain-cache/`.
- **Domain cache entries must come from WebSearch results only.** Never write cache entries based on model knowledge alone. If WebSearch is unavailable, skip cache persistence entirely.
- **Analyze every discovered item.** Skip none.
- **Apply the rubric strictly.** Do not inflate grades.
- **Every recommendation must include a concrete rewrite** — not just "improve X."
- **Present all reports before asking** about follow-up actions.
- **Error handling:** If an analysis agent fails, report the failure with partial results and continue with remaining items. Never silently skip.
