---
name: check-repo-health
description: >
  Verify reference file freshness (90-day cycles), token budget compliance,
  and cross-skill reference integrity. Produces a health dashboard with
  pass/warn/fail status per check. Use for routine monitoring of a skills
  repository or before running reviews.
argument-hint: "[all|freshness|tokens|integrity]"
allowed-tools: Read, Glob
---

# Check Repo Health

You are a repository health monitor checking for staleness, budget violations, and broken references. Your job is to surface maintenance needs before they affect skill quality.

## Workflow

### 1. Parse arguments and load thresholds

Parse `$ARGUMENTS` for which checks to run. Valid values: `all` (default), `freshness`, `tokens`, `integrity`. If the argument is not recognized, default to `all`.

Read `references/health-thresholds.md` for configurable thresholds. If the file cannot be read, use built-in defaults (freshness: 60/90 days, token budgets: rubric 1000, baseline 2000, others 500, usage tiers: 80%/100%) and note the fallback in the dashboard header.

### 2. Discover files

Use Glob to build a file inventory:
- `.claude/skills/*/SKILL.md` — repo-internal skill files
- `.claude/skills/*/references/*.md` — repo-internal reference files
- `.claude/skills/*/references/domain-cache/*.md` — repo-internal domain cache entries
- `skills/*/SKILL.md` — plugin skill files
- `skills/*/references/*.md` — plugin reference files
- `skills/*/references/domain-cache/*.md` — plugin domain cache entries
- `research/**/*.md` — all research files
- `CLAUDE.md` — project instructions

### 3. Check freshness (if `all` or `freshness`)

For each reference file with a `last_refreshed` field in its YAML frontmatter:
1. Read the file and extract the `last_refreshed` date.
2. Compute the number of days since refresh (from today's date).
3. Classify: **PASS** (<60 days), **WARN** (60-89 days), **FAIL** (≥90 days).

For domain cache entries, use the dates from `domain-cache/INDEX.md` (read once, extract all dates) rather than reading each cache file individually.

Record results as rows in the freshness table.

### 4. Check token budgets (if `all` or `tokens`)

For each reference file, read its content and estimate tokens as `character_count / 4` (approximate).

Apply thresholds from `health-thresholds.md` (loaded in step 1). Use the file pattern → budget mapping from the Token Budgets table.

Classify: **PASS** (<80% of budget), **WARN** (80-100% of budget), **FAIL** (>100% of budget).

Record results as rows in the tokens table.

### 5. Check reference integrity (if `all` or `integrity`)

Perform three integrity sub-checks:

**5a. CLAUDE.md Research References**
Read the `## Research References` section of CLAUDE.md. For each linked path (e.g., `research/prompt-engineering/prompt-engineering-techniques.md`), Glob to verify the file exists. Record PASS or FAIL per link.

**5b. CLAUDE.md Architecture / Structure**
Read the `## Architecture` section of CLAUDE.md. If `## Architecture` is missing, fall back to one alias in this order: `## Structure`, `## Layout`, `## File Structure`. For each file path or directory path mentioned in the chosen section, Glob to verify it exists. Record PASS or FAIL per path. If none of these sections exist, record one FAIL row for the missing section rather than erroring out.

**5c. Cross-skill references**
For each SKILL.md, search the body for paths referencing sibling skills or shared reference files (patterns like `../`, `references/`, or sibling skill names). For each reference found, Glob to verify the target file exists. Record PASS or FAIL per reference.

### 6. Present dashboard

Present all results in a consolidated dashboard:

```
## Repository Health Dashboard

**Date:** YYYY-MM-DD
**Checks run:** [list of checks]

### Freshness
| File | Last Refreshed | Days | Status |
|------|---------------|------|--------|
| engineering-baseline.md | 2026-03-24 | 0 | PASS |

### Token Budgets
| File | Estimated Tokens | Budget | Usage | Status |
|------|-----------------|--------|-------|--------|
| scoring-rubric.md | ~450 | 1000 | 45% | PASS |

Note: Token estimates use chars/4 approximation.

### Reference Integrity
| Source | Reference | Status |
|--------|-----------|--------|
| CLAUDE.md | research/prompt-engineering/... | PASS |

---

**Summary:** X passed, Y warnings, Z failures
```

If any FAIL or WARN results exist, add a **Remediation** section:
- For stale files: "Run `/refresh-engineering-baseline`" or "Domain cache entry X is N days old — will be refreshed on next review run."
- For token budget violations: "File X is ~N tokens over the N-token budget. Consider trimming."
- For broken references: "Path X referenced in Y does not exist. Update the reference or create the file."

Then end your response with this menu:

---
**What's next?**
1. Refresh stale baseline → `/refresh-engineering-baseline`
2. Run a full review → `/review-claude-config`
3. Done

_Type a number to continue._

---

When the user responds: **1** → invoke `/refresh-engineering-baseline`. **2** → invoke `/review-claude-config`. **3** → acknowledge and stop.

If all checks passed (no FAIL or WARN), skip the menu — just present the dashboard.

## Hard Rules

- **Read-only.** Never modify any file. This is a diagnostic skill only.
- **Always show all results.** Present the full dashboard even if everything passes.
- **Token estimation is approximate.** Always note that chars/4 is an approximation in the output.
- **Graceful with missing files.** If a reference file cannot be read, report it as FAIL with a note, do not error out.
