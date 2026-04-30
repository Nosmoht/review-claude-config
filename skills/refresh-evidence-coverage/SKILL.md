---
name: refresh-evidence-coverage
description: >
  Re-audits the dimension-evidence coverage matrix on a quartärly (90-day)
  cadence by running per-dimension web research against documented anchor
  queries, integrating new Tier-1 sources into rubric/baseline/research
  files. Use when asked to 'refresh evidence coverage' or '/refresh-evidence-coverage'.
  Do NOT use for fresh research synthesis without prior coverage matrix —
  use /audit-context-budget or per-dimension issues instead.
argument-hint: "[dimension|all]"
allowed-tools: Read, Write, Edit, Glob, Grep, WebSearch, WebFetch
disable-model-invocation: true
---

# Refresh Evidence Coverage

This skill maintains `docs/dimension-evidence-coverage.md` as a living artifact. It runs the per-dimension Tier-1 source audit at a quartärly cadence, integrates new findings, and surfaces gaps as follow-up issues.

## Argument Handling

- `$ARGUMENTS` is either a single dimension name (`Clarity`, `Completeness`, `Prompt Engineering`, `Context Engineering`, `Goal Alignment`, `Safety`, `Metadata`) OR `all` (iterate all 7) OR empty (default to `all`).
- Validate: if `$ARGUMENTS` is non-empty and not in the dimension set / `all`, list valid choices and stop.

## Workflow

### Step 1: Load Coverage Matrix and Cadence Doc

Read these files JIT:
- `docs/dimension-evidence-coverage.md` — current matrix with `last_audited:` per dimension
- `docs/evidence-maintenance.md` §"Quartärly Evidence-Coverage Cadence" — anchor queries per dimension
- `~/.claude/workspace/claude-config/rules/web-research.md` — search budget and Tier-1 filter

### Step 2: Determine Audit Scope

For each dimension to audit (`$ARGUMENTS` or all 7):
1. Read the dimension's `last_audited:` value
2. If today minus `last_audited` < 90 days AND user did not pass `--force`, skip with status `up-to-date`
3. Otherwise, this dimension is in scope for refresh

### Step 3: Per-Dimension Audit (atomic per dimension)

For each in-scope dimension:

**Apply only the search anchors** for that dimension as documented in `evidence-maintenance.md` §"Per-Dimension Search Strategy".

Execute web research per the global `web-research.md` rule:
- ≥2 query formulations per anchor
- Max 3 cycles
- Tier-1 filter: peer-reviewed / arXiv / foundation-lab; ≥50 citations OR ≤18 months old
- Cross-validation: ≥2 independent sources per new claim

Compare findings against the dimension's "Last anchored to" sources in the matrix:
- **No new Tier-1 sources found**: write a one-line null-result entry to `Plans/refresh-evidence-coverage-<date>.md`. Update `last_audited:` to today.
- **New Tier-1 sources found**: open a focused follow-up issue per source (or per cluster) using the #91-cycle template. Do NOT operationalize inline — operationalization is per-issue work with adversarial review per `docs/change-discipline-rule.md`.

### Step 4: Update Coverage Matrix

For each dimension audited:
1. Update `last_audited:` per-dimension entry in the matrix table
2. Update Tier-1 source count and grounded-item count if a follow-up issue subsequently lands new items
3. Re-compute coverage score: `(grounded_items + 1) / (total_rubric_items + 1)` (Laplace-smoothed)

Per the rubric/baseline freeze rule (`CLAUDE.md` "Mid-session rubric/baseline freeze"): do NOT edit `scoring-rubric.md` or `engineering-baseline.md` mid-session. Surface findings as issues; operationalization happens in fresh sessions per the documented atomic commit pattern.

### Step 5: Output

Write a refresh report to `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/refresh-evidence-coverage-<date>.md` with:
- Audit date
- Dimensions audited (skipped: list)
- Per-dimension findings (new sources / null result)
- Issues opened (with #IDs)
- Next audit date (today + 90 days)

## Completion

You are done when:
- Every in-scope dimension has been audited (or skipped with reason)
- `docs/dimension-evidence-coverage.md` `last_audited:` frontmatter fields are updated to the current date for each audited dimension
- New-source findings are tracked as issues (operationalization deferred to fresh sessions)
- Refresh report written and reported to user

If a Tier-1 source surfaces that *contradicts* an existing rubric item (e.g., literature establishes a different primitive than the existing item assumes), set `last_audited:` for that dimension AND open a `priority: P1` issue with the contradiction. Never silently keep a refuted heuristic.

## Hard Rules

- **Do NOT operationalize new sources inline.** Surface as issues; defer to per-issue commits with adversarial review.
- **Do NOT edit scoring-rubric.md or engineering-baseline.md mid-session.** Cache-prefix invariant per CLAUDE.md.
- **Do NOT skip the Tier-1 filter.** Tutorials, blog posts without metrics, and Stack Overflow answers do not satisfy web-research rule.
- **Always cite the search-trail** in the refresh report — queries tried, sources rejected, why.
