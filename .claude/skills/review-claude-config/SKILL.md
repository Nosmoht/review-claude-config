---
name: review-claude-config
description: >
  Analyze and optimize all Claude Code skills, agents, and rules in a project's
  .claude/ directory. Applies evidence-based prompt and context engineering
  evaluation with type-appropriate scoring dimensions, produces per-item quality
  certificates with concrete optimization recommendations. Use when you want to
  audit skill/agent/rule quality or before shipping new skills.
argument-hint: [folder]
allowed-tools: Agent, Read, Write, Glob, WebSearch, WebFetch
---

# Review Claude Config

Analyze all Claude Code skills, agents, and rules in a target folder and produce per-item quality certificates with optimization recommendations.

## Argument Handling

- `$ARGUMENTS` is the target folder path. If empty, use the current working directory.
- Validate the folder exists. If no `.claude/` directory is found at any level, report that and stop.

## Phase 1 — Setup and Discovery

### Step 0: Tool Availability Checks

Attempt a trivial WebSearch (e.g., "Claude Code documentation"). If it fails or is unavailable, set `websearch_available = false` and continue. Goal Alignment will be scored from model knowledge only, marked `[no web verification]` on the certificate.

Attempt a trivial WebFetch (e.g., fetch "https://docs.anthropic.com"). If it fails or is unavailable, set `webfetch_available = false` and continue. Analysis agents will use WebSearch snippets only instead of fetching full article content.

### Steps 1-2: Launch in parallel

**1. Load References**

Read these files from the skill's own `references/` directory:
- `references/scoring-rubric.md` — the grading criteria
- `references/engineering-baseline.md` — prompt, context, and tool design techniques

Check `last_refreshed` date in the baseline frontmatter. If older than 3 months, warn the user: "Baseline was last refreshed on [date]. Consider running `/refresh-engineering-baseline` for current best practices."

**2. Discovery Agent**

Launch an Agent (allowed-tools: Glob, Read) to discover all skills, agents, and rules in the target folder:

```
Discover all Claude Code skills, agents, and rules. Use Glob with these patterns:
- <folder>/.claude/skills/*/SKILL.md
- <folder>/.claude/agents/*.md
- <folder>/.claude/rules/*.md
- <folder>/**/.claude/skills/*/SKILL.md (monorepo support)
- <folder>/**/.claude/agents/*.md (monorepo support)
- <folder>/**/.claude/rules/*.md (monorepo support)

Exclude paths containing: node_modules, .git, vendor, dist, build, .claude/reviews

For each discovered file:
- Read the full content
- Classify as "Skill", "Agent", or "Rule"
- Return: file path, type, full content

Also note (but do not analyze): existence of CLAUDE.md, .claude/settings.json
```

If no skills, agents, or rules are discovered, report that and stop.

## Phase 2 — Per-Item Analysis

### Step 0: Domain Cache Lookup

Before dispatching analysis agents, the orchestrator performs domain cache lookup:

1. **Load knowledge base index.** Read `references/domain-cache/INDEX.md`. If missing or empty, skip to step 3 (all items get MISS status and proceed with WebSearch as normal).

2. **Match or infer domain keys.** For each discovered item, determine its domain:
   - Present the full INDEX.md table (keys + descriptions) as context.
   - For each item, ask: "Which existing knowledge base entry best matches this item's domain? If none fit, generate a new key (lowercase-hyphenated, 2-4 words)."
   - **Prefer reuse:** An existing key is always better than generating a new one that means the same thing. E.g., if `kubernetes` exists in the index and a skill targets Kubernetes, use `kubernetes` — do not generate `k8s` or `kube-orchestration`.
   - If ambiguous between existing entries, prefer the more specific one (e.g., `argocd` over `gitops`). If ambiguous between existing and new, prefer existing.
   - If no clear domain is inferable (e.g., a generic "code-review" or "commit" skill), skip cache lookup for that item and use current behavior (WebSearch or model knowledge).
   - **Normalization pass (fallback):** After all items, review the full list and normalize near-duplicates (e.g., collapse `react-test` and `react-testing` to the more specific form).
   - For each matched/new key: check `last_refreshed` date in INDEX.md. **CACHED** (<90 days), **STALE** (≥90 days), or **MISS** (new key, not in index).
   - For CACHED/STALE: read the full `references/domain-cache/{domain-key}.md` on-demand. If index says CACHED but the file is missing, treat as MISS.

3. **Assign one researcher per domain.** For STALE/MISS domains shared by multiple items, designate only **one** analysis agent as the "researcher" for that domain. Other agents sharing the same domain are told: "Another agent is researching this domain — use cached content or model knowledge, do not WebSearch for domain research."

### Step 1: Dispatch Analysis Agents

For each discovered item, launch an analysis Agent with allowed-tools: WebSearch, WebFetch, Read (no Write, Edit, or Bash). If `webfetch_available = false`, omit WebFetch from the agent's allowed-tools. Process in parallel, batched in groups of 8 (if more than 8 items). Present each batch's results before starting the next. Partial final batches are handled identically.

Each analysis agent receives a **byte-identical shared prefix** (rubric + baseline content) followed by per-item specifics. This preserves KV-cache hits across agents.

### Analysis Agent Prompt Template

```
You are evaluating a Claude Code [Skill/Agent/Rule] for quality.

Tools available: WebSearch (for domain research), WebFetch (for reading full article
content from URLs found via WebSearch), and Read. Do not use Write, Edit, or Bash.
You are evaluating, not modifying.

[If WebFetch is unavailable, omit it from this line.]

## Reference Materials

### Scoring Rubric
[Insert scoring-rubric.md content here]

### Engineering Baseline
[Insert engineering-baseline.md content here]

## Item Under Review

**Type:** [Skill/Agent/Rule]
**Path:** [file path]
**Content:**
[Insert full file content here]

[If Type is Agent, add:]
## Agent-Specific Evaluation Notes
- **Metadata:** Evaluate `model` field appropriateness (haiku/sonnet/opus vs task complexity per Model Selection Conventions in the format research).
- **Context Engineering:** Evaluate description and example blocks for activation precision, not progressive disclosure (agents are single-file).
- **Completeness:** Evaluate `<example>` blocks for trigger pattern coverage.

[If Type is Rule, add:]
## Rule-Specific Evaluation
Rules use only 3 dimensions (renormalized to 100%):
- **Clarity (30%):** Is the rule unambiguous? Could two models interpret it differently?
- **Completeness (30%):** Are edge cases and scope boundaries defined?
- **Goal Alignment (40%):** Does the rule achieve its stated constraint?
Skip: Prompt Engineering, Context Engineering, Safety, Metadata (rules have no tools, no frontmatter, and are directives not prompts). Use the Rule certificate format below.

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
3. **Full-Content Retrieval (when WebFetch is available):**
   After WebSearch returns results, identify the 1-2 most relevant URLs
   (prefer primary sources: official docs, peer-reviewed papers, production
   case studies). Fetch each with WebFetch using a targeted prompt:
   "Extract domain best practices, benchmarks, and configuration patterns
   relevant to [domain]. Max 500 words."
   Use the full content — not just search snippets — when synthesizing
   domain knowledge and writing Domain Cache Update sections.
   If WebFetch is unavailable, proceed with search snippets as before.
4. Synthesize: what should a high-quality item in this domain include?

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

[If Type is Rule, use this certificate table instead:]

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | [A-F] | 30% | [One line] |
| Completeness | [A-F] | 30% | [One line] |
| Goal Alignment | [A-F] | 40% | [One line] |
| **Overall** | **[A-F]** | **100%** | **Weighted: XX.X** |

Calculate: Weighted score = Clarity×.30 + Completeness×.30 + GoalAlignment×.40.
Convert and map back using the same grade scale (A=95, B=85, etc.).

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
| ... | Skill/Agent | ... | ... | ... | ... | ... | ... | ... | ... |
| ... | Rule | ... | ... | ... | — | — | ... | — | — |
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
6. If `websearch_available = false` and `webfetch_available = false`, skip this entire phase — never write cache entries from model knowledge alone.
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
    type: Skill                          # Skill, Agent, or Rule
    path: relative/path/to/file
    overall: B
    score: 85.0
    clarity: B
    completeness: A
    prompt_engineering: B                # null for Rules
    context_engineering: B               # null for Rules
    goal_alignment: B
    safety: A                            # null for Rules
    metadata: B                          # null for Rules
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
- **Domain cache entries must come from web research (WebSearch and/or WebFetch) only.** Never write cache entries based on model knowledge alone. If WebSearch is unavailable, skip cache persistence entirely.
- **Analyze every discovered item.** Skip none.
- **Apply the rubric strictly.** Do not inflate grades.
- **Every recommendation must include a concrete rewrite** — not just "improve X."
- **Present all reports before asking** about follow-up actions.
- **Error handling:** If an analysis agent fails, report the failure with partial results and continue with remaining items. Never silently skip.
