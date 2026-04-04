---
name: check-repo-health
description: >
  Verify reference file freshness (90-day cycles), token budget compliance,
  and cross-skill reference integrity. Produces a health dashboard with
  pass/warn/fail status per check. Use for routine monitoring of a skills
  repository or before running reviews.
argument-hint: "[all|freshness|tokens|integrity] [--validation]"
allowed-tools: Read, Glob
---

# Check Repo Health

You are a repository health monitor checking for staleness, budget violations, and broken references. Your job is to surface maintenance needs before they affect skill quality.

## Workflow

### 1. Parse arguments and load thresholds

Parse `$ARGUMENTS` for:
- `validation_mode = true` if the standalone token `--validation` is present
- the check selector among `all`, `freshness`, `tokens`, `integrity`

Remove `--validation` before interpreting the selector. If the remaining selector is not recognized or empty, default to `all`.

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

For each reference or research file with a `last_refreshed` field in its YAML frontmatter:
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

Perform four integrity sub-checks in normal mode and three deterministic sub-checks in validation mode.

**5a. CLAUDE.md Research References**
Read the `## Research References` section of CLAUDE.md. For each linked path (e.g., `research/prompt-engineering/prompt-engineering-techniques.md`), Glob to verify the file exists. Record PASS or FAIL per link.

**5b. CLAUDE.md Architecture / Structure**
Read the `## Architecture` section of CLAUDE.md. If `## Architecture` is missing, fall back to one alias in this order: `## Structure`, `## Layout`, `## File Structure`. For each file path or directory path mentioned in the chosen section, Glob to verify it exists. Record PASS or FAIL per path. If none of these sections exist, record one FAIL row for the missing section rather than erroring out.

**5c. Cross-skill references**

**5c-i. Registry check.** Read `references/cross-skill-dependencies.md`. Extract the `**Base:**` prefix value. For each row in the dependency table:
1. Expand comma-separated Source values into individual source entries.
2. Resolve Target path: if it starts with `skills/`, use as-is; otherwise prepend Base.
3. Glob for the resolved Target path.
4. Record the result using the row's Severity symbol:
   - `!` target missing → **FAIL**
   - `?` target missing → **WARN**
   - `-` target missing → **PASS** (informational only)
   - Target exists → **PASS**

If the registry file cannot be read, note the fallback in the dashboard header and skip to 5c-ii.

**5c-ii. Heuristic scan.** For each SKILL.md (across both `skills/` and `.claude/skills/`), search the body for paths referencing sibling skills or shared reference files (patterns like `../`, `**/`, `references/`, or sibling skill names). For each reference found:
1. Glob to verify the target file exists.
2. Check whether this source→target pair already appears in the registry.
3. Record: **PASS** (exists, registered), **FAIL** (missing), or **UNREGISTERED** (exists but not in registry — add it to `references/cross-skill-dependencies.md`).

If `validation_mode = true`, skip 5c-ii entirely. Validation mode is the deterministic release gate and must not emit exploratory `UNREGISTERED` findings from the heuristic scan.

**5d. Review-contract consistency**
Locate the canonical review contract and rubric via Glob:
- `**/review-claude-config/references/review-report-contract.md`
- `**/review-claude-config/references/scoring-rubric.md`

Prefer the `skills/review-claude-config/references/` copies when present. Otherwise use the sibling `.claude/skills/review-claude-config/references/` copies.

Read those files as the canonical review/report contract and rubric. Extract the full set of summary dimensions from the contract and the rule subset from `## Rule-Specific Scoring`.

Then read each consumer file and verify its dimensions match the expected set:

| Consumer file | Expected set | How dimensions appear |
|---|---|---|
| `skills/review-analytics/references/report-schema.md` | Canonical contract reference present | Pointer to `review-report-contract.md` |
| `skills/review-skill/SKILL.md` | Full | Dimension column values in the certificate table template (exclude the "Overall" row — it is a computed aggregate, not a dimension) |
| `skills/review-agent/SKILL.md` | Full | Same as review-skill |
| `skills/review-rule/SKILL.md` | Rule subset | Same format, fewer dimensions |
| `skills/review-analytics/SKILL.md` | Full (snake_case) | Dimension field names referenced in the report parsing instructions |
| `skills/review-claude-config/SKILL.md` | Full (with abbreviations: PE=Prompt Engineering, CE=Context Engineering, Goal=Goal Alignment, Meta=Metadata) | Column headers in the summary table template |
| `CLAUDE.md` | Full | Parenthetical list in the opening paragraph |
| `skills/apply-review-findings/SKILL.md` | Canonical contract reference present | Parse instructions reference `review-report-contract.md` |
| `skills/apply-skill-review-findings/SKILL.md` | Canonical contract reference present | Parse instructions reference `review-report-contract.md` |
| `skills/apply-agent-review-findings/SKILL.md` | Canonical contract reference present | Parse instructions reference `review-report-contract.md` |
| `skills/apply-rule-review-findings/SKILL.md` | Canonical contract reference present | Parse instructions reference `review-report-contract.md` |
| `docs/skills/apply-review-findings.md` | Runtime/doc alignment | Low-impact handling and contract-reference behavior match runtime |
| `docs/skills/apply-skill-review-findings.md` | Runtime/doc alignment | Dispatchable/manual-only and Low-impact behavior match runtime |
| `docs/skills/apply-agent-review-findings.md` | Runtime/doc alignment | Dispatchable/manual-only and canonical path authority match runtime |
| `docs/skills/apply-rule-review-findings.md` | Runtime/doc alignment | Dispatchable/manual-only and Low-impact behavior match runtime |
| `docs/skills/review-analytics.md` | Runtime/doc alignment | Discovery scope and series identity rules match runtime |
| `docs/skills/review-skill.md` | Canonical contract reference present | Review contract wording matches runtime |
| `docs/skills/review-agent.md` | Canonical contract reference present | Review contract wording matches runtime |
| `docs/skills/review-rule.md` | Canonical contract reference present | Review contract wording matches runtime |
| `docs/skills/review-claude-config.md` | Canonical contract reference present | Review contract wording matches runtime |

For dimension-based consumers: PASS if all expected dimensions are present and no unexpected dimensions appear. FAIL if any dimension is missing or extra, noting which ones.

For contract-reference consumers: PASS if they explicitly reference `review-report-contract.md` as the canonical source. FAIL if they still present themselves as an independent schema authority or omit the contract reference.

For runtime/doc alignment consumers:
- `docs/skills/apply-review-findings.md` must match runtime on Low-impact behavior and manual-only/dispatchable distinction.
- `docs/skills/apply-skill-review-findings.md`, `docs/skills/apply-agent-review-findings.md`, and `docs/skills/apply-rule-review-findings.md` must match runtime on dispatchable/manual-only behavior. The agent doc must also match runtime on canonical `summary.path` authority.
- `docs/skills/review-analytics.md` must match runtime on report discovery scope, validation-mode truncation order, producer-scoped rename/move logic, and the distinction between artifact identity (`type + path`) and analytics series identity (`generated_by + type + path`).
- Record FAIL if docs describe narrower discovery, different low-impact handling, or omit manual-only behavior now present in runtime.

Record results in the Reference Integrity table with Source = consumer file path, Reference = `review-report-contract.md` or `scoring-rubric.md`, Status = PASS or FAIL (with mismatch details if FAIL).

### 6. Present dashboard

If `validation_mode = true`, present a bounded dashboard:

```markdown
## Repository Health Dashboard

**Date:** YYYY-MM-DD
**Checks run:** [list]
**Mode:** validation

**Counts:** X PASS | Y WARN | Z FAIL

### Non-PASS Findings
| Source | Reference | Status |
|--------|-----------|--------|
| ... | ... | WARN/FAIL |
```

In validation mode:
- include only non-PASS rows
- omit the heuristic-scan `UNREGISTERED` class entirely
- omit the follow-up menu

Otherwise present the normal full dashboard below.

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
- For dimension mismatches: "Consumer X has [missing/extra] dimensions vs the canonical review contract/rubric. Update the consumer to match."
- For contract-reference mismatches: "Consumer X does not point to `review-report-contract.md` as the canonical schema. Remove duplicated schema authority."

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
