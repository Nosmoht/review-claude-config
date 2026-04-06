---
name: review-claude-config
description: >
  Audits all skills, agents, and rules in a folder and produces quality
  certificates. Use when asked to 'audit quality', 'review skills', or before
  shipping new skills. Do NOT use for a single item — use /review-skill,
  /review-agent, or /review-rule.
argument-hint: "[folder] [--validation]"
allowed-tools: Agent, Read, Write, Glob, WebSearch, WebFetch
---

# Review Claude Config

Analyze all Claude Code skills, agents, and rules in a target folder and produce per-item quality certificates with optimization recommendations.

## Argument Handling

Parse `$ARGUMENTS` into:
- `validation_mode = true` if the standalone token `--validation` is present
- `target_folder` = the remaining argument text after removing `--validation`

If `target_folder` is empty, use the current working directory.

Validate the folder exists. If no `.claude/` directory is found at any level, report that and stop.

Validation mode is a bounded release/CI path. It is not the default user flow.

## Phase 1 — Setup and Discovery

### Step 0: Tool Availability Checks

If `validation_mode = true`:
- set `websearch_available = false`
- set `webfetch_available = false`
- skip live tool probes entirely

Otherwise:
- Attempt a trivial WebSearch (e.g., "Claude Code documentation"). If it fails or is unavailable, set `websearch_available = false` and continue. Goal Alignment will be scored from model knowledge only, marked `[no web verification]` on the certificate.
- Attempt a trivial WebFetch (e.g., fetch "https://docs.anthropic.com"). If it fails or is unavailable, set `webfetch_available = false` and continue. Analysis agents will use WebSearch snippets only instead of fetching full article content.

### Steps 1-2: Launch in parallel

**1. Load References**

Read these files from the skill's own `references/` directory:
- `references/scoring-rubric.md` — the grading criteria
- `references/engineering-baseline.md` — prompt, context, and tool design techniques with canonical evidence-class labels
- `references/source-quality-criteria.md` — source credibility criteria for web research

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

Return results in this exact format per item:

### [file path]
**Type:** Skill | Agent | Rule
**Content:**
[full file content]

If a file cannot be read, return:
### [file path]
**Type:** Unknown
**Error:** [reason]

If a Glob pattern returns no results, skip it silently (not all repos have all types).

Also note (but do not analyze): existence of CLAUDE.md, .claude/settings.json

COMPLETION: You are done when all Glob patterns have been checked and all readable files are classified.
```

If no skills, agents, or rules are discovered, report that and stop.

Sort the discovered items lexicographically by file path before returning them to the orchestrator.

## Phase 2 — Per-Item Analysis

### Step 0: Domain Cache Lookup

If `validation_mode = true`, skip the cache workflow entirely:
- assign every item `Domain: none`
- assign `Cache Status: NONE`
- assign `Role: consumer`
- do not load `domain-cache/INDEX.md`
- do not infer domains
- do not designate researchers
- do not persist cache updates later

Otherwise continue with the normal cache workflow below.

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

### Step 1: Load Specialized Skill Content

Locate the specialized review skills (sibling directories in the same plugin). Use Glob if paths are not immediately known: `**/review-skill/SKILL.md`, `**/review-agent/SKILL.md`, `**/review-rule/SKILL.md`.

Read the SKILL.md and evaluation guide for each type that has discovered items:
- Skills: `review-skill/SKILL.md` + `review-skill/references/skill-evaluation-guide.md`
- Agents: `review-agent/SKILL.md` + `review-agent/references/agent-evaluation-guide.md`
- Rules: `review-rule/SKILL.md` + `review-rule/references/rule-evaluation-guide.md`

Only load the types that have discovered items (e.g., skip agent content if no agents found).

### Step 2: Dispatch Analysis Agents

Group discovered items by type (Skill, Agent, Rule). For each type group, construct a **type-specific shared prefix** that is **byte-identical** across all items of the same type. This maximizes KV-cache hits within each type group.

**Type-specific shared prefix structure:**
```
[Specialized SKILL.md instructions for this type]

## Reference Materials

### Scoring Rubric
[Insert scoring-rubric.md content — identical across all types]

### Engineering Baseline
[Insert engineering-baseline.md content — identical across all types]

### Source Quality Criteria
[Insert source-quality-criteria.md content — identical across all types]

### Type-Specific Evaluation Guide
[Insert the evaluation guide for this type]
```

**Per-item suffix** (appended after the shared prefix):

```
---orchestration---
mode: orchestrated
websearch_available: [true/false]
webfetch_available: [true/false]
domain_cache: |
  [cached domain content, "none", or full cache protocol instructions:]
  Domain: [domain key or "none"]
  Cache Status: [CACHED | STALE | MISS | NONE]
  Role: [researcher | consumer]

  [If CACHED: insert cached content + "Use as domain knowledge, skip WebSearch.
  1 supplemental query if insufficient."]

  [If STALE + researcher: insert cached content + "Use as starting point +
  1 WebSearch to verify/update. Apply discard rules from source-quality-criteria.md.
  Tag each source with tier (1/2/3). Return Domain Cache Update section."]

  [If STALE + consumer: insert cached content + "Use as-is, another agent
  is refreshing."]

  [If MISS + researcher: "No cache. 1 WebSearch query. Apply discard rules
  from source-quality-criteria.md. Tag each source with tier (1/2/3). Return
  Domain Cache Update section."]

  [If MISS + consumer: "No cache. Use model knowledge only."]

  [If NONE: "No domain inferred. WebSearch as normal."]
---

## Item Under Review

**Path:** [file path]
**Content:**
[Insert full file content]
```

If `validation_mode = true`, select a deterministic validation sample before dispatch:
- take the first lexicographic Skill, if any
- then the first lexicographic Agent, if any
- then the first lexicographic Rule, if any
- if fewer than 3 items were selected, fill the remaining slots with the next lexicographic undispatched items regardless of type
- analyze at most 3 items total

**Dispatch rules:**
- Allowed-tools per agent: WebSearch, WebFetch, Read (no Write, Edit, or Bash). Omit WebFetch if `webfetch_available = false`.
- If `validation_mode = true`, dispatch the sampled items in a single batch and do not present intermediate per-batch output.
- Otherwise process in parallel, batched in groups of 8. Present each batch's results before starting the next.
- Each agent returns a structured certificate (or an `## ERROR` block on failure).
- On agent error: log failure, continue with remaining items.

### Domain Cache Update Collection

After all agents complete, collect "Domain Cache Update" sections from researcher agents that had STALE or MISS cache status. Hold these for Phase 3.5.

If `validation_mode = true`, skip this collection step entirely.

## Phase 3 — Presentation

If `validation_mode = true`, do not print full per-item reports. Instead present only:

```markdown
## Validation Summary

- Mode: validation
- Target: <folder>
- Items discovered: N
- Items analyzed: M
- Sampled paths:
  - <path 1>
  - <path 2>
  - <path 3>

| Item | Type | Overall | Score |
|------|------|---------|-------|
| ... | ... | ... | ... |
```

If any sampled item returns an `## ERROR` block, surface it directly under `## Validation Summary`.

Skip the normal full report presentation, Cross-Cutting Observations, Phase 3.5, Phase 4, and the follow-up menu in validation mode.

Otherwise continue with the normal presentation below.

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
- Where possible, cite one concrete example path per pattern so the observation is easy to verify

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
    tier: [1|2|3]
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

If `validation_mode = true`, skip this entire phase.

After presenting all reports to the user, confirm before writing:
"Save review report to `<target>/.claude/reviews/YYYY-MM-DDTHHMMSS-review-claude-config.md`?"

If the user declines, skip report writing but still display the report path that would have been used.

### Step 1: Assemble report

Construct a Markdown file with canonical YAML frontmatter from `references/review-report-contract.md` and a full body.

Required producer-specific values:
- `generated_by: review-claude-config`
- one `summary` entry per discovered item
- `type + path` as the canonical portfolio identity
- `null` for rule-only non-applicable dimensions

**Body:** All per-item reports (Goal + Certificate + Strengths + Recommendations), Summary Table, Cross-Cutting Observations.

For every High or Medium recommendation in the body, preserve the shared recommendation schema from `references/review-report-contract.md`.

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

### Step 5: What's Next?

After all output is complete, end your response with this menu (substitute `<report-path>` with the actual report path from step 2):

---
**What's next?**
1. Apply review findings → `/apply-review-findings <report-path>`
2. View grade analytics → `/review-analytics`
3. Done

_Type a number to continue._

---

When the user responds: **1** → invoke `/apply-review-findings` with the report path. **2** → invoke `/review-analytics`. **3** → acknowledge and stop.

## Hard Rules

- **Read-only on analyzed files.** Never modify any discovered skill, agent, or reference file. The only files this skill writes are the review report at `<target>/.claude/reviews/YYYY-MM-DDTHHMMSS-review-claude-config.md` and domain cache entries in its own `references/domain-cache/`.
- **Domain cache entries must come from web research (WebSearch and/or WebFetch) only.** Never write cache entries based on model knowledge alone. If WebSearch is unavailable, skip cache persistence entirely.
- **Analyze every discovered item.** Skip none in the normal mode. Validation mode is the only exception and must stay capped at the deterministic sample described above.
- **Apply the rubric strictly.** Do not inflate grades.
- **Every High or Medium recommendation must include evidence and a concrete rewrite** — not just "improve X."
- **Present all reports before asking** about follow-up actions.
- **Error handling:** If an analysis agent fails, report the failure with partial results and continue with remaining items. Never silently skip.
