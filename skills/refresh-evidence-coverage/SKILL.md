---
name: refresh-evidence-coverage
description: >
  Re-audits the dimension-evidence coverage matrix by running per-dimension
  web research against documented anchor queries, integrating new Tier-1
  sources into rubric/baseline/research files. Triggered manually via
  `/refresh-evidence-coverage [dimension|all]`. Use when
  `docs/dimension-evidence-coverage.md` shows `last_audited` >90 days for the
  target dimension, or when a new Tier-1 paper for that dimension is added
  under `research/`. Do NOT use for fresh research synthesis without a prior
  coverage matrix — use /audit-context-budget or per-dimension issues instead.
argument-hint: "[dimension|all]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch
disable-model-invocation: true
---

# Refresh Evidence Coverage

This skill maintains `docs/dimension-evidence-coverage.md` as a living artifact. It runs the per-dimension Tier-1 source audit at a quartärly cadence, integrates new findings, and surfaces gaps as follow-up issues.

## Argument Handling

- `$ARGUMENTS` is either a single dimension name (`Clarity`, `Completeness`, `Prompt Engineering`, `Context Engineering`, `Goal Alignment`, `Safety`, `Metadata`) OR `all` (iterate all 7) OR empty (default to `all`).
- Validate: if `$ARGUMENTS` is non-empty and not in the dimension set / `all`, list valid choices and stop.

## Workflow

### Step 1: Resolve Repo Slug and Load Coverage Matrix

Resolve `<repo-slug>` by running `bash bin/repo-slug.sh "$(pwd)"` and capturing stdout. (For documentation reference only, not the operational source-of-truth: `references/repo-identification.md` describes the sanitize algorithm.)

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
- **No new Tier-1 sources found**: post a one-line null-result comment on the relevant tracking issue + update `last_audited:` to today. Working notes are session-local (no file commit).
- **New Tier-1 sources found**: open a focused follow-up issue per source (or per cluster) using the #91-cycle template. Do NOT operationalize inline — operationalization is per-issue work with adversarial review per `docs/change-discipline-rule.md`.

### Step 4: Update Coverage Matrix

For each dimension audited:
1. Update `last_audited:` per-dimension entry in the matrix table
2. Update Tier-1 source count and grounded-item count if a follow-up issue subsequently lands new items
3. Re-compute coverage score: `(grounded_items + 1) / (total_rubric_items + 1)` (Laplace-smoothed)

Per the rubric/baseline freeze rule (`CLAUDE.md` "Mid-session rubric/baseline freeze"): do NOT edit `scoring-rubric.md` or `engineering-baseline.md` mid-session. Surface findings as issues; operationalization happens in fresh sessions per the documented atomic commit pattern.

### Step 5: Output

Write a refresh report to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/refresh-evidence-coverage-<date>.md` with:
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

## Quality measurement (mandatory before Output)

Per `docs/skill-verification-architecture.md` (2026-05-26 retrofit), MAINTAIN-class verification is deterministic: schema invariants (canonical `YYYY-MM-DD` `last_audited:`, frozen-file guard), idempotency `f(f(x)) == f(x)` (re-run within 90 days is a no-op), and freshness predicates (90-day cadence) fully cover this skill's failure surface. There is no judgment-shaped output to evaluate, so the historical Layer B (adversarial critic) and Layer C (binary rubric) were dropped — they added token cost and false-positive surface without raising assurance. Layer A below is the complete verification.

This skill produces (a) mutations to `docs/dimension-evidence-coverage.md`, (b) tracking issues created via `gh`, and (c) a refresh-report at `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/refresh-evidence-coverage-<date>.md`. Layer A idempotency must be checked with `last_audited` rolled back to >90 days (otherwise the freshness gate early-returns and the test is trivial). External-dependency drift is acknowledged — idempotency is relaxed to "no mutations beyond those traceable to a recorded fetch event".

Snapshot the pre-run and post-run state for the matrix file, the refresh report, and the freshness window for each in-scope dimension so subsequent steps can compare deterministically:

```bash
TMPDIR=$(mktemp -d -t rec-XXXX)
PRE_MATRIX="$TMPDIR/coverage-matrix.pre.md"
POST_MATRIX="$TMPDIR/coverage-matrix.post.md"
POST2_MATRIX="$TMPDIR/coverage-matrix.post2.md"
REPORT="$TMPDIR/refresh-report.md"
# Copy docs/dimension-evidence-coverage.md to PRE_MATRIX before Step 4.
# After Step 4, copy the mutated file to POST_MATRIX.
# Re-invoke the skill on POST_MATRIX state (without rolling last_audited back)
# and capture to POST2_MATRIX — this is the idempotency probe.
# Copy the refresh report written in Step 5 to REPORT.
```

### Layer A — mechanical invariants (deterministic, fail-fast)

Run against PRE / POST / POST2 matrix snapshots and the refresh report. `STRICT` rows abort with exit 1; `SOFT` rows warn and continue.

```bash
python3 - "$PRE_MATRIX" "$POST_MATRIX" "$POST2_MATRIX" "$REPORT" <<'PY'
import sys, re
from pathlib import Path

PRE, POST, POST2, REPORT = (Path(p) for p in sys.argv[1:5])

DIMS = {"Clarity", "Completeness", "Prompt Engineering", "Context Engineering",
        "Goal Alignment", "Safety", "Metadata"}
CANONICAL_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LAST_AUDITED_LINE = re.compile(r"last_audited\s*:\s*(\S+)")
TRACKING_ISSUE_RE = re.compile(r"#(\d+)")

def read(p): return p.read_text(errors="ignore") if p.exists() else ""

pre, post, post2, report = read(PRE), read(POST), read(POST2), read(REPORT)
rows = []  # (sev, metric, before, after, delta, flag)

# STRICT-1 IDEMPOTENCY — second run within 90 days of last_audited MUST be no-op
# (modulo whitelisted timestamp fields like generated_at). Compare POST vs POST2
# stripping only obvious run-id lines.
def canonicalize(text):
    return re.sub(r"^(?:generated_at|run_id|report_timestamp)\s*[:=]\s*\S+\s*$",
                  "", text, flags=re.M)
idem_delta = 1 if canonicalize(post) != canonicalize(post2) else 0
rows.append(("STRICT", "idempotent_rerun_diff",
             0, idem_delta, f"+{idem_delta}" if idem_delta else "0",
             " FAIL second_run_mutated_matrix" if idem_delta else ""))

# STRICT-2 DATE_FORMAT — every last_audited: value in POST is YYYY-MM-DD
bad_dates = [v for v in LAST_AUDITED_LINE.findall(post)
             if not CANONICAL_DATE.match(v)]
rows.append(("STRICT", "last_audited_date_format_violations",
             0, len(bad_dates), f"+{len(bad_dates)}" if bad_dates else "0",
             f" FAIL non_canonical={bad_dates[:5]}" if bad_dates else ""))

# STRICT-3 FROZEN_FILE_GUARD — refresh report MUST NOT claim or evidence
# inline mutation of scoring-rubric.md or engineering-baseline.md
frozen_hits = re.findall(
    r"\b(?:scoring-rubric\.md|engineering-baseline\.md)\b[^.\n]{0,60}"
    r"(?:edited|updated|mutated|modified|rewrote|patched)",
    report, re.I)
# Also check the matrix diff: a mid-session run touching either frozen file
# is itself the breach (the skill could have written via Edit/Write).
frozen_in_post = bool(re.search(
    r"\b(?:scoring-rubric\.md|engineering-baseline\.md)\b\s*[:=]\s*(?:edited|updated)",
    post, re.I))
breach = len(frozen_hits) + (1 if frozen_in_post else 0)
rows.append(("STRICT", "frozen_file_breach_claims",
             0, breach, f"+{breach}" if breach else "0",
             f" FAIL hits={frozen_hits[:3]}" if breach else ""))

# STRICT-4 MATRIX_DIMENSION_SET — every audited dimension present in POST
# matches the canonical set; no rogue rows added.
post_dims = set(re.findall(
    r"^\|\s*(Clarity|Completeness|Prompt Engineering|Context Engineering|"
    r"Goal Alignment|Safety|Metadata)\s*\|", post, re.M))
missing = DIMS - post_dims
rogue_rows = re.findall(r"^\|\s*([A-Z][A-Za-z ]+?)\s*\|\s*\d", post, re.M)
rogue = [r for r in rogue_rows if r not in DIMS]
rows.append(("STRICT", "matrix_dimension_set_violations",
             7, len(post_dims),
             f"-{len(missing)}+{len(rogue)}" if (missing or rogue) else "0",
             f" FAIL missing={sorted(missing)} rogue={rogue[:3]}"
             if (missing or rogue) else ""))

# SOFT-1 ISSUES_VS_SOURCES — every tracking issue cited in the report
# should pair with a search-trail citation (queries + sources). If issues
# outnumber distinct cited sources by >2, flag for operator glance.
issues = set(TRACKING_ISSUE_RE.findall(report))
arxiv_cites = set(re.findall(r"arXiv:\d+\.\d+", report))
url_cites = set(re.findall(r"https?://\S+", report))
src_count = len(arxiv_cites) + len(url_cites)
flag = ""
if issues and len(issues) > src_count + 2:
    flag = f" warn issues={len(issues)} cited_sources={src_count}"
rows.append(("SOFT", "issues_vs_cited_sources",
             0, len(issues), f"+{len(issues)}", flag))

# SOFT-2 LAST_AUDITED_FORWARD_MOTION — every dimension's last_audited
# in POST is >= the corresponding PRE value (never moves backward).
def last_audited_by_dim(text):
    out = {}
    for line in text.splitlines():
        m = re.match(
            r"^\|\s*(Clarity|Completeness|Prompt Engineering|Context Engineering|"
            r"Goal Alignment|Safety|Metadata)\s*\|.*?\|\s*(\d{4}-\d{2}-\d{2})\s*\|",
            line)
        if m: out[m.group(1)] = m.group(2)
    return out
pre_dates = last_audited_by_dim(pre)
post_dates = last_audited_by_dim(post)
backward = [d for d in post_dates
            if d in pre_dates and post_dates[d] < pre_dates[d]]
rows.append(("SOFT", "last_audited_backward_motion",
             0, len(backward), f"+{len(backward)}",
             f" warn dims={backward}" if backward else ""))

fail = 0
print(f"{'severity':9} {'metric':40} {'before':>8} {'after':>8} {'delta':>10}")
for sev, metric, before, after, delta, flag in rows:
    if "FAIL" in flag: fail += 1
    print(f"{sev:9} {metric:40} {str(before):>8} {str(after):>8} {delta:>10}{flag}")
sys.exit(1 if fail else 0)
PY
```

If exit non-zero → STOP, do not finalize the refresh. Report failures and propose specific restorations (re-write the bad `last_audited:` value in canonical format, revert any mutation to the frozen files, re-include the dropped dimension row), then re-run Layer A on the patched matrix.

### Reconciliation outcomes

- **All STRICT pass** → finalize the refresh. Write the report, commit the matrix update, surface follow-up issues.
- **Any STRICT fail** → propose targeted restorations (re-write the bad `last_audited:` value in canonical format, revert any inline mutation of frozen files, restore the dropped dimension row, pair the orphan tracking issue with its search-trail) and re-run Layer A on the patched state. **Hard cap: 2 iterations** (per `rules/contract-authoring.md §Small-bound carve-out`; bound = 2 → hard rule, no graceful +1). If still failing after iteration 2, surface to the user; do not auto-publish the refresh.
- **Only SOFT warnings** (`issues_vs_cited_sources` skew, `last_audited_backward_motion`) → finalize but surface the warnings in the refresh-report Summary line so the operator has a final-glance opportunity.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **External-dependency drift.** This skill consults `WebSearch` / `WebFetch` to discover new Tier-1 sources; the same repo state on different days can legitimately yield different mutations because the external corpus moved. Idempotency is relaxed to "no mutations beyond those traceable to a recorded fetch event in the refresh report".
2. **Semantic correctness of "new Tier-1 source".** Layer A treats the Tier-1 filter (peer-reviewed / arXiv / foundation-lab; ≥50 citations OR ≤18 months old) as a self-contained predicate; misclassification of a blog-post-with-arXiv-shaped-URL is operator review at the issue-triage step.
3. **Cross-session state corruption.** The mid-session-freeze rule (CLAUDE.md §Hard Constraints #6) is enforced against the refresh report's claims and the POST matrix diff; a skill that edited a frozen file via sub-shell and forgot to record it would pass STRICT-3 (no claim) yet still violate the rule. Builder-agent session-state guard surfaces this.

## Hard Rules

- **Do NOT operationalize new sources inline.** Surface as issues; defer to per-issue commits with adversarial review.
- **Do NOT edit scoring-rubric.md or engineering-baseline.md mid-session.** Cache-prefix invariant per CLAUDE.md.
- **Do NOT skip the Tier-1 filter.** Tutorials, blog posts without metrics, and Stack Overflow answers do not satisfy web-research rule.
- **Always cite the search-trail** in the refresh report — queries tried, sources rejected, why.

## Tier A Tool Justification

**Tier A tool justification (Bash):** Bash is granted exclusively for
`bash bin/repo-slug.sh "$(pwd)"` to compute the canonical `<repo-slug>`
deterministically per `references/repo-identification.md`. The
command-level allowlist `Bash(bash bin/repo-slug.sh:*)` enforces scope.
The script is read-only (stdout slug, no FS writes), so this Tier-A grant
carries no write-amplification risk.
