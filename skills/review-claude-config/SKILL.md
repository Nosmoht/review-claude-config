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

Launch an Agent (allowed-tools: Glob, Read) to discover all Claude Code primitives in the target folder:

```
Discover all Claude Code skills, agents, rules, MCP server configs, and settings. Use Glob/Read with these patterns:
- <folder>/.claude/skills/*/SKILL.md
- <folder>/.claude/agents/*.md
- <folder>/.claude/rules/*.md
- <folder>/**/.claude/skills/*/SKILL.md (monorepo support)
- <folder>/**/.claude/agents/*.md (monorepo support)
- <folder>/**/.claude/rules/*.md (monorepo support)
- <folder>/.mcp.json (MCP server config)
- <folder>/.claude/settings.json (project settings)
- <folder>/.claude/settings.local.json (local settings, if exists)

Exclude paths containing: node_modules, .git, vendor, dist, build, reports

For each discovered file:
- Read the full content
- Classify as "Skill", "Agent", "Rule", "MCP", or "Settings"

Return results in this exact format per item:

### [file path]
**Type:** Skill | Agent | Rule | MCP | Settings
**Content:**
[full file content]

If a file cannot be read, return:
### [file path]
**Type:** Unknown
**Error:** [reason]

If a Glob pattern returns no results, skip it silently (not all repos have all types).

Also note (but do not analyze): existence of CLAUDE.md

COMPLETION: You are done when all Glob patterns have been checked and all readable files are classified.
```

If no primitives are discovered at all, report that and stop.

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

1. **Load knowledge base index.** Read `references/domain-cache/INDEX.md`. INDEX.md contains only universal methodology entries (context-engineering, research-sourcing, etc.). Domain-specific knowledge is researched at runtime.

2. **Match items against universal cache.** For each discovered item:
   - Match against the INDEX.md entries (keys + descriptions).
   - If a universal entry matches: check `last_refreshed` date. **CACHED** (<90 days), **STALE** (≥90 days). Read `references/domain-cache/{key}.md` on-demand. If file is missing despite being in INDEX.md, downgrade to RUNTIME_RESEARCH.
   - If no universal entry matches: extract the single most specific technology or workflow term from (1) frontmatter description, (2) parent directory name, (3) explicit technology references in body. If multiple candidates, prefer the term appearing in both description and body. Assign status **RUNTIME_RESEARCH**.
   - If no clear domain is inferable (e.g., generic "code-review"): assign `Domain: none`, `Cache Status: NONE`.

3. **Assign researchers.** For STALE universal entries shared by multiple items, designate one agent as researcher (existing pattern). For RUNTIME_RESEARCH domains, designate one researcher per unique domain keyword.

### Step 0b: Domain Deep Research (parallel with Step 1; Step 2 waits for both to complete)

If any items have `RUNTIME_RESEARCH` status and `websearch_available = true`:

1. From the discovery results (Phase 1) and the detected runtime domain keywords, derive 2-3 **specific** research questions. Not generic "best practices" — targeted questions from the repo context. Examples:
   - Technology: "SwiftUI AudioSession best practices for recording + offline storage"
   - Workflow: "corpus canonization quality criteria for chat exports"
   - Quality: "requirement traceability validation patterns for specification documents"
2. Launch a Domain Research Agent (allowed-tools: WebSearch, WebFetch, Read) that executes 2-3 WebSearch queries per domain (max 5 total, hard cap). Apply `source-quality-criteria.md` discard rules. Tag each source with tier.
3. Collect structured domain knowledge per domain (max 500 tokens each).
4. This research is **ephemeral** — it is injected into the per-item orchestration suffix but NOT persisted to disk.

If `websearch_available = false`, skip this step. Items with RUNTIME_RESEARCH proceed with model knowledge only.

### Step 1: Load Specialized Skill Content

Locate the specialized review skills (sibling directories in the same plugin). Use Glob if paths are not immediately known.

Read the SKILL.md and evaluation guide for each type that has discovered items:
- Skills: `review-skill/SKILL.md` + `review-skill/references/skill-evaluation-guide.md`
- Agents: `review-agent/SKILL.md` + `review-agent/references/agent-evaluation-guide.md`
- Rules: `review-rule/SKILL.md` + `review-rule/references/rule-evaluation-guide.md`
- MCP: `review-mcp-server/SKILL.md` + `review-mcp-server/references/mcp-evaluation-guide.md`
- Settings: `review-settings/SKILL.md` + `review-settings/references/settings-evaluation-guide.md`

Only load the types that have discovered items (e.g., skip MCP content if no `.mcp.json` found).

### Step 2: Dispatch Analysis Agents

Group discovered items by type (Skill, Agent, Rule, MCP, Settings). For each type group, construct a **type-specific shared prefix** that is **byte-identical** across all items of the same type. MCP and Settings are typically single-item groups (one `.mcp.json`, one `settings.json` per repo) — dispatch as batch of 1, same pattern.

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
  Domain: [domain key or "none"]
  Cache Status: [CACHED | STALE | RUNTIME_RESEARCH | NONE]
  Role: [researcher | consumer]

  [If CACHED: insert cached content + "Use as domain knowledge, skip WebSearch.
  1 supplemental query if insufficient."]

  [If STALE + researcher: insert cached content + "Use as starting point +
  1 WebSearch to verify/update. Apply discard rules from source-quality-criteria.md.
  Tag each source with tier (1/2/3). Return Domain Cache Update section."]

  [If STALE + consumer: insert cached content + "Use as-is, another agent
  is refreshing."]

  [If RUNTIME_RESEARCH + research available: insert runtime research content +
  "Use as domain context. This research is ephemeral — do NOT return a
  Domain Cache Update section."]

  [If RUNTIME_RESEARCH + no research: "No cache. Use model knowledge only."]

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

After all agents complete, collect "Domain Cache Update" sections from researcher agents that had STALE cache status for universal entries only. RUNTIME_RESEARCH results are ephemeral and must NOT be collected for persistence. Hold updates for Phase 3.5.

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
| ... | MCP | ... | — | ... | — | — | ... | ... | ... |
| ... | Settings | ... | — | ... | — | — | ... | ... | ... |
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
2. Collect "Domain Cache Update" sections from researcher agents. **Only persist updates for domains already listed in INDEX.md** (universal entries). Do not create new domain-cache entries from runtime research — it is ephemeral by design.
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
"Save review report to `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-review-claude-config.md`?"

Resolve `<repo-slug>` per `references/repo-identification.md`. Include `repo: <slug>` and optionally `origin: <git-remote-url>` in frontmatter.

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

Write to: `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-review-claude-config.md`

Use the current date and time for the timestamp. Create the `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/` directory if it does not exist. Timestamp ensures each run produces a unique file, supporting the "iterate until convergence" workflow.

### Step 3: Delta comparison

If a previous review report exists in `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/`:
- Read the most recent prior report's frontmatter `summary` block and `baseline_version`
- **Baseline check:** If the prior report's `baseline_version` differs from the current engineering baseline, apply the Baseline version lock hard rule (present choice to user before proceeding)
- Compare each item's current grades against prior grades
- Append a "Delta from Prior Review" section to the report body:

```
## Delta from Prior Review ([prior report date])

| Item | Dimension | Previous | Current | Change |
|------|-----------|----------|---------|--------|
| [only rows where grades changed] |
```

If the prior report contains `finding_id` values in recommendation headings, also append a finding-level delta:

```
## Finding Delta from Prior Review

| finding_id | Status | Prior Impact | Current Impact |
|------------|--------|-------------|----------------|
| [rows for: new, recurring, fixed, regressed] |
```

Status definitions (SARIF/SonarQube pattern):
- **new:** finding_id in current but NOT in prior
- **recurring:** finding_id in BOTH current AND prior
- **fixed:** finding_id in prior but NOT in current
- **regressed:** finding_id was `verified` in prior `.finding-state` section but reappears as FAIL

If the prior report has no finding_ids, skip the finding delta (backward-compatible).

If no prior report exists, skip this step entirely.

### Step 4: Confirm

Tell the user the report file path and suggest committing with: `docs(reviews): add YYYY-MM-DDTHHMMSS review report` (using the timestamp from the report filename). This ensures the docs commit and subsequent fix commits (`fix(<scope>): address findings from YYYY-MM-DDTHHMMSS review`) share the same identifier for traceability.

### Step 5: What's Next?

After all output is complete, present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Apply review findings" (Recommended) — description: `"Run /apply-review-findings <report-path> to address High/Medium findings"`
- Option 2 label: "View grade analytics" — description: `"Run /review-analytics to track quality trends over time"`
- Option 3 label: "Done" — description: `"End the workflow"`

On "Apply review findings": invoke `/apply-review-findings` with the report path. On "View grade analytics": invoke `/review-analytics`. On "Done": acknowledge and stop.

## Hard Rules

- **Read-only on analyzed files.** Never modify any discovered skill, agent, or reference file. The only files this skill writes are the review report at `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-review-claude-config.md` and domain cache entries in its own `references/domain-cache/`.
- **Domain cache entries must come from web research (WebSearch and/or WebFetch) only.** Never write cache entries based on model knowledge alone. If WebSearch is unavailable, skip cache persistence entirely.
- **Analyze every discovered item.** Skip none in the normal mode. Validation mode is the only exception and must stay capped at the deterministic sample described above.
- **Apply the rubric strictly.** Do not inflate grades.
- **Every High or Medium recommendation must include evidence and a concrete rewrite** — not just "improve X."
- **Present all reports before asking** about follow-up actions.
- **Error handling:** If an analysis agent fails, report the failure with partial results and continue with remaining items. Never silently skip.
- **Baseline version lock.** When a prior review report exists for the same target directory, use the same `baseline_version` as the prior report. If the current engineering baseline is newer, present the user with a choice: "Prior review used baseline v{prior}. Current baseline is v{current}. Use [prior|current]?" A baseline change is equivalent to a rubric change and must be a conscious decision, not an implicit drift.
