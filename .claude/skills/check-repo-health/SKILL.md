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

Read `references/health-thresholds.md` for configurable thresholds.

### 2. Discover files

Use Glob to build a file inventory:
- `.claude/skills/*/SKILL.md` — all skill files
- `.claude/skills/*/references/*.md` — all reference files
- `.claude/skills/*/references/domain-cache/*.md` — domain cache entries
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

Apply thresholds from `health-thresholds.md`:
- `scoring-rubric.md` — budget: 1000 tokens
- `engineering-baseline.md` — budget: 2000 tokens
- `signal-catalog.md` — budget: 1000 tokens
- Domain cache entries (`domain-cache/*.md`, excluding INDEX.md) — budget: 500 tokens each
- Other reference files — budget: 500 tokens (default)

Classify: **PASS** (<80% of budget), **WARN** (80-100% of budget), **FAIL** (>100% of budget).

Record results as rows in the tokens table.

### 5. Check reference integrity (if `all` or `integrity`)

Perform three integrity sub-checks:

**5a. CLAUDE.md Research References**
Read the `## Research References` section of CLAUDE.md. For each linked path (e.g., `research/prompt-engineering/prompt-engineering-techniques.md`), Glob to verify the file exists. Record PASS or FAIL per link.

**5b. CLAUDE.md File Structure**
Read the `## File Structure` section of CLAUDE.md. For each file path mentioned, Glob to verify it exists. Record PASS or FAIL per path.

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

If any FAIL results exist, add a **Remediation** section:
- For stale files: "Run `/refresh-engineering-baseline`" or "Domain cache entry X is N days old — will be refreshed on next review run."
- For token budget violations: "File X is ~N tokens over the N-token budget. Consider trimming."
- For broken references: "Path X referenced in Y does not exist. Update the reference or create the file."

## Hard Rules

- **Read-only.** Never modify any file. This is a diagnostic skill only.
- **Always show all results.** Present the full dashboard even if everything passes.
- **Token estimation is approximate.** Always note that chars/4 is an approximation in the output.
- **Graceful with missing files.** If a reference file cannot be read, report it as FAIL with a note, do not error out.
