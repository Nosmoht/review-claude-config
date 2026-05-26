---
name: check-repo-health
description: >
  Verifies reference freshness, token budgets, and cross-skill reference
  integrity. Use for 'check health', routine monitoring, or before running
  reviews. Do NOT use for skill quality or trends — use /review-claude-config
  or /review-analytics.
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

**5a. Research References Index**
Read `docs/research-references.md` (the canonical research-index file). For each Markdown link entry `- [Title](path)`, resolve the path **relative to `docs/`** (e.g., `(../research/prompt-engineering/prompt-engineering-techniques.md)` → `<target>/research/prompt-engineering/prompt-engineering-techniques.md`). Glob to verify the resolved file exists. Record PASS or FAIL per link. If `docs/research-references.md` is missing entirely, record one FAIL row noting that the canonical index is absent.

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
| `skills/review-claude-config/references/report-schema.md` | Canonical contract reference present | Pointer to `review-report-contract.md` |
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
| docs/research-references.md | research/prompt-engineering/... | PASS |

---

**Summary:** X passed, Y warnings, Z failures
```

If any FAIL or WARN results exist, add a **Remediation** section:
- For stale files: "Run `/refresh-engineering-baseline`" or "Domain cache entry X is N days old — will be refreshed on next review run."
- For token budget violations: "File X is ~N tokens over the N-token budget. Consider trimming."
- For broken references: "Path X referenced in Y does not exist. Update the reference or create the file."
- For dimension mismatches: "Consumer X has [missing/extra] dimensions vs the canonical review contract/rubric. Update the consumer to match."
- For contract-reference mismatches: "Consumer X does not point to `review-report-contract.md` as the canonical schema. Remove duplicated schema authority."

If any checks have FAIL or WARN status, present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Refresh stale baseline" (Recommended) — description: `"Run /refresh-engineering-baseline to update the engineering baseline"`
- Option 2 label: "Run a full review" — description: `"Run /review-claude-config to audit all skills and rules"`
- Option 3 label: "Done" — description: `"End the workflow"`

On "Refresh stale baseline": invoke `/refresh-engineering-baseline`. On "Run a full review": invoke `/review-claude-config`. On "Done": acknowledge and stop.

If all checks passed (no FAIL or WARN), skip the menu — just present the dashboard.

## Quality measurement (mandatory before Output)

Per `docs/skill-verification-architecture.md` (2026-05-26 retrofit), MAINTAIN-class verification is deterministic: schema invariants, idempotency `f(f(x)) == f(x)`, and freshness predicates against documented day-count windows fully cover this skill's failure surface. There is no judgment-shaped output to evaluate, so the historical Layer B (adversarial critic) and Layer C (binary rubric) were dropped — they added token cost and false-positive surface without raising assurance. Layer A below is the complete verification.

This skill produces a verdict dashboard (no file write) with a mode selector. Layer A idempotency MUST be checked **per-mode** — an `all` run and a `freshness` run are different observables.

Capture the dashboard output (and, if available, the prior-run snapshot) to a tempdir so subsequent steps can read both deterministically:

```bash
TMPDIR=$(mktemp -d -t crh-XXXX)
CURRENT="$TMPDIR/current-dashboard.md"
# Write the dashboard the skill just produced to "$CURRENT".
# If a prior dashboard snapshot is available, export PRE_VERDICT=<path>;
# otherwise leave unset and SOFT-2 row is skipped.
MODE="$1"   # one of: all | freshness | tokens | integrity
```

### Layer A — mechanical invariants (deterministic, fail-fast)

Run against the produced dashboard, the prior snapshot (if any), and a second invocation in the same mode on unchanged input. `STRICT` rows abort; `SOFT` rows warn and continue.

```bash
python3 - "$CURRENT" "${PRE_VERDICT:-/dev/null}" "$MODE" <<'PY'
import sys, re, os
from pathlib import Path

CURRENT, PRE_VERDICT, MODE = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]

VERDICT_STATUSES = {"PASS", "WARN", "FAIL", "BLOCKED", "SKIPPED", "up-to-date", "UNREGISTERED"}
# Modes that are expected to emit each table.
TABLE_FOR_MODE = {
    "all":        {"Freshness", "Token Budgets", "Reference Integrity"},
    "freshness":  {"Freshness"},
    "tokens":     {"Token Budgets"},
    "integrity":  {"Reference Integrity"},
}

text = CURRENT.read_text(errors="ignore")
rows = []  # (sev, metric, before, after, delta, flag)

# STRICT-1 VERDICT_STATUS_VOCAB — every status token must be in the closed set
status_cells = re.findall(r"\|\s*(PASS|WARN|FAIL|BLOCKED|SKIPPED|up-to-date|UNREGISTERED|[A-Z][A-Z_-]+)\s*\|", text)
bad = [s for s in status_cells if s not in VERDICT_STATUSES]
rows.append(("STRICT", "verdict_status_vocab_violations",
             0, len(bad), f"+{len(bad)}" if bad else "0",
             f" FAIL unknown={sorted(set(bad))[:5]}" if bad else ""))

# STRICT-2 MODE_TABLE_PRESENCE — required tables for the selected mode are present
expected = TABLE_FOR_MODE.get(MODE, set())
present = {h for h in ("Freshness", "Token Budgets", "Reference Integrity")
           if re.search(rf"^###\s+{re.escape(h)}\s*$", text, re.M)}
missing = expected - present
rows.append(("STRICT", "mode_table_presence",
             len(expected), len(present),
             f"-{len(missing)}" if missing else "0",
             f" FAIL missing={sorted(missing)}" if missing else ""))

# STRICT-3 VERDICT_ROW_EVIDENCE — every dashboard row cites a Source/File
# column with a non-empty path. Catches D5 VERDICT_HONESTY violations
# (rows with empty evidence pointers).
empty_evidence = 0
for line in text.splitlines():
    if not line.startswith("|") or line.startswith("|--") or line.startswith("|---"): continue
    cells = [c.strip() for c in line.split("|")[1:-1]]
    if len(cells) < 2: continue
    if cells[0] in ("File", "Source", "Consumer") or set(cells[0]) <= {"-"}: continue
    if not cells[0]:
        empty_evidence += 1
rows.append(("STRICT", "rows_without_evidence_pointer",
             0, empty_evidence, f"+{empty_evidence}" if empty_evidence else "0",
             f" FAIL empty_evidence_rows={empty_evidence}" if empty_evidence else ""))

# SOFT-1 VERDICT_ROW_COUNT_DELTA — vs prior snapshot (NULL_VERDICT_REGRESSION smell)
if PRE_VERDICT.exists() and str(PRE_VERDICT) != "/dev/null":
    prev = PRE_VERDICT.read_text(errors="ignore")
    prev_rows = len(re.findall(r"^\|", prev, re.M))
    curr_rows = len(re.findall(r"^\|", text, re.M))
    delta = curr_rows - prev_rows
    flag = ""
    if prev_rows and abs(delta) >= max(5, prev_rows // 4):
        flag = f" warn prev={prev_rows} curr={curr_rows}"
    rows.append(("SOFT", "verdict_row_count_delta",
                 prev_rows, curr_rows, f"{delta:+d}", flag))

# SOFT-2 NON_PASS_TOTAL — count of WARN+FAIL+UNREGISTERED rows (operator glance)
non_pass = sum(1 for s in status_cells if s in {"WARN", "FAIL", "UNREGISTERED"})
rows.append(("SOFT", "non_pass_rows", 0, non_pass, f"+{non_pass}", ""))

fail = 0
print(f"{'severity':9} {'metric':40} {'before':>8} {'after':>8} {'delta':>8}")
for sev, metric, before, after, delta, flag in rows:
    if "FAIL" in flag: fail += 1
    print(f"{sev:9} {metric:40} {str(before):>8} {str(after):>8} {delta:>8}{flag}")
sys.exit(1 if fail else 0)
PY
```

Then run the same mode a **second time on the unchanged repo** and diff the two dashboard outputs (modulo the `**Date:**` and any explicit `generated_at`-class lines). Any non-whitespace delta → STRICT-IDEMPOTENT fail.

If exit non-zero → STOP, do not present the dashboard. Report failures and propose specific restorations (re-include dropped row class, fix status-vocab cell), then re-run Layer A.

### Reconciliation outcomes

- **All STRICT pass** → present the dashboard.
- **Any STRICT fail** → propose targeted restorations (restore the dropped row, fix the bad status cell, expand the mode table to include the missing class) and re-run Layer A on the patched dashboard. **Hard cap: 2 iterations** (per `rules/contract-authoring.md §Small-bound carve-out`; bound = 2 → hard rule, no graceful +1). If still failing after iteration 2, surface to the user; do not auto-publish the dashboard.
- **Only SOFT warnings** (`verdict_row_count_delta` jump, large `non_pass_rows` total) → present the dashboard but include the warnings in the Summary line so the operator has a final-glance opportunity.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **External-dependency drift.** `references/health-thresholds.md` itself may diverge from upstream sources. Layer A treats the thresholds file as authoritative; if it is stale, every downstream verdict is stale-by-reference. Mitigation lives in the 90-day cadence on the thresholds file itself.
2. **Timestamp parser silent coercion.** If the date parser silently coerces a malformed `last_refreshed:` value to today's date, Layer A sees 0 days since refresh and judges PASS legitimate. The fix is parser hardening at the skill body, not at the verification layer.
3. **Dashboard-to-actual-repo divergence.** Layer A compares the dashboard against the thresholds file and the prior dashboard; it does not re-walk the filesystem to confirm a PASS row's `last_refreshed:` value matches the file today. A stale read inside the skill body is invisible to the pipeline.

## Hard Rules

- **Read-only.** Never modify any file. This is a diagnostic skill only.
- **Always show all results.** Present the full dashboard even if everything passes.
- **Token estimation is approximate.** Always note that chars/4 is an approximation in the output.
- **Graceful with missing files.** If a reference file cannot be read, report it as FAIL with a note, do not error out.
