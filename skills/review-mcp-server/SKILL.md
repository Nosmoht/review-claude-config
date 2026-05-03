---
name: review-mcp-server
description: >
  Evaluates MCP server configuration (.mcp.json manifest, transport,
  servers-block) across 4 dimensions (Completeness, Goal Alignment, Safety,
  Metadata). Use when asked to 'review mcp', 'review mcp server', or
  'review .mcp.json'. Do NOT use for skills, agents, rules, hooks, or
  settings.json.
argument-hint: <path-to-.mcp.json>
allowed-tools: Read, Write, Glob, Grep, WebSearch
---

# Review MCP Server Configuration

Evaluate a `.mcp.json` file for quality across 4 evidence-based dimensions. Reviews the whole file with per-server-entry iteration.

## Argument Handling

- `$ARGUMENTS` is a path to a `.mcp.json` file.
- If the path points to a directory, look for `.mcp.json` in the project root.
- If no `.mcp.json` found, report the error and stop.
- Parse the JSON. If parsing fails, report as a Critical finding and stop.

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

1. **Load references.** Read:
   - Scoring rubric: Glob `**/review-claude-config/references/scoring-rubric.md`
   - Source quality criteria: Glob `**/review-claude-config/references/source-quality-criteria.md`
   - Repo identification: Glob `**/review-claude-config/references/repo-identification.md` to resolve `suite-root` and `repo-slug`
   - MCP evaluation guide: `skills/review-claude-config/references/mcp-evaluation-guide.md`

2. **Probe tool availability.** Test WebSearch with a trivial query. Record `websearch_available`.

## Phase 2 — Evaluation

### Step A: Context Inference + Domain Research

1. Read the `.mcp.json` file. Count servers. Identify project context from surrounding repo (read `CLAUDE.md` or `README.md` if available).
2. Domain research (follow orchestration flags if in orchestrated mode):
   - Check the domain cache: Read `${CLAUDE_PLUGIN_ROOT}/skills/review-claude-config/references/domain-cache/INDEX.md` and match to a universal cache entry.
   - If `CACHED` (≤90 days): use cache as primary knowledge.
   - If `STALE`: perform 1 WebSearch to refresh.
   - If no cache entry matches: perform 1-2 targeted WebSearch queries (MCP server security + configuration quality, not generic "best practices"). Fetch the top result if available.
   - If unavailable: use model knowledge only, marked `[no external verification]`.
   - Apply source quality criteria.
3. Synthesize: what should a well-configured `.mcp.json` for this project include?

### Step B: Checklist Evaluation

1. Load `skills/review-claude-config/references/mcp-evaluation-guide.md`.
2. For each server entry in `.mcp.json`, evaluate every checklist item: PASS | FAIL | NA.
3. Aggregate across all server entries. A single FAIL on any server = FAIL for that item.
4. Score each dimension using the rubric. Cite evidence before grading.
   - Grade derivation: A=0 FAILs; B=≤25% (no High); C=any High or >25%; D=>50% High; F=>50% total.
5. Calculate overall grade using 4-dimension weights: Completeness 25%, Goal Alignment 25%, Safety 30%, Metadata 20%.

### Step C: Output

Produce the certificate:

```
### Goal
[One sentence: what this .mcp.json should achieve]

### Certificate

| Dimension | Grade | Weight | Key Evidence |
|-----------|-------|--------|--------------|
| Completeness | [grade] | 25% | [checklist IDs] |
| Goal Alignment | [grade] | 25% | [checklist IDs] |
| Safety | [grade] | 30% | [checklist IDs] |
| Metadata | [grade] | 20% | [checklist IDs] |
| **Overall** | **[grade]** | | **[score]** |

### Strengths
- [up to 3 bullet points]

### Recommendations
[For each FAIL with High/Medium impact:]
#### N. [Title] (Impact: [H/M/L], Category: [...], ID: {checklist-item}:{path}:{dim}/v1)
**Evidence:** [exact quote or reference]
**Why it matters:** [impact explanation]
**Validation:** [how to verify the fix]
**Current:** [current config snippet]
**Recommended:** [fixed config snippet]
```

## Phase 3 — Report (standalone mode only)

Before Write: scan the assembled report (frontmatter `target:`, optional `origin:`, and the entire body including per-finding evidence quotations) and replace any literal absolute home-directory prefix with `$HOME/`. The `~/.claude/hooks/block-sensitive-content.sh` PreToolUse hook denies Writes containing such prefixes.
1. Write the review report to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-review-mcp-server.md` with frontmatter matching the review report contract. Include `repo: <slug>` and optionally `origin: <git-remote-url>` in the frontmatter (after `date`). Create the `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/` directory if it does not exist.
2. Suggest commit message: `docs(reviews): add YYYY-MM-DDTHHMMSS MCP server review report`.

## Hard Rules

- **Read-only on analyzed files.** Never modify `.mcp.json`. Write only to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`.
- **Apply the rubric strictly.** Do not inflate grades.
- **Every High or Medium recommendation must include evidence and a concrete rewrite.**
- **Parse failure = Critical.** Invalid JSON is the most dangerous finding (all subsequent checks are meaningless).
