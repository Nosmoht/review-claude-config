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

Without verification, this skill fails at **RECURSIVE_DISCIPLINE_BREACH** — the skill is the named gateway to evidence-coverage refresh, and a successful run that silently edited `scoring-rubric.md` or `engineering-baseline.md` inline would violate `CLAUDE.md §Hard Constraints #6` (mid-session freeze) — the very rule the skill exists to honor. A second dominant failure class is **STATE_FORMAT_DRIFT** in `last_audited:` (a value written as `2026/05/25` instead of `2026-05-25` breaks the downstream regex parser in `check-repo-health freshness`). A third is **IDEMPOTENCY_BREAK**: a re-run within 90 days of `last_audited` must early-return with `up-to-date` status and zero mutations — otherwise every re-invocation gratuitously bumps the matrix. A three-layer pipeline (mechanical invariants / adversarial critic / binary rubric) is required because no single layer catches all three classes.

References: CheckEval (arXiv:2403.18771), G-Eval (arXiv:2303.16634), Position bias in LLM-as-a-Judge (arXiv:2406.07791), IFEval (arXiv:2311.07911), FollowBench (ACL 2024), Beyond Consensus (NUS 2025). Per-skill design: `.work/skill-verification/maintain-template.md §Per-skill customization notes`.

Per the MAINTAIN template's per-skill note: this skill produces (a) mutations to `docs/dimension-evidence-coverage.md` (per-dim `last_audited:` bumps + coverage scores), (b) tracking issues created via `gh`, and (c) a refresh-report at `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/refresh-evidence-coverage-<date>.md`. Layer A idempotency must be checked with `last_audited` rolled back to >90 days (otherwise the freshness gate early-returns and the test is trivial). External-dependency drift (residual #5) applies — D1 is relaxed to "no mutations beyond those traceable to a recorded fetch event". Layer B's dominant risk is RECURSIVE_DISCIPLINE_BREACH (the skill MUST NOT edit `scoring-rubric.md` or `engineering-baseline.md` inline). D1, D2, D4, D5 carry the highest weight; D3 covers matrix ↔ rubric consistency; D6 N/A.

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

### Layer B — adversarial critic dispatch (blind, recall-framed)

Dispatch a fresh subagent with the **single task** of finding what was lost or wrongly mutated. Adversarial framing is the layer that catches RECURSIVE_DISCIPLINE_BREACH (mid-session inline edit) and STALE_MISS / FALSE_STALE classes. Seed the critic with `CLAUDE.md §Hard Constraints` and `references/evidence-contract.md` so judgments are evaluated against documented conventions, not the critic's prior.

```
Agent({
  description: "Adversarial refresh-evidence-coverage critic",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind reviewer auditing a refresh-evidence-coverage skill run. " +
    "You are given:\n" +
    "  A: <pre-run snapshot of docs/dimension-evidence-coverage.md>\n" +
    "  B: <post-run snapshot of the same file>\n" +
    "  V: <the refresh-report markdown the skill produced>\n" +
    "  C: <CLAUDE.md §Hard Constraints + §Mid-session rubric/baseline freeze>\n" +
    "  E: <references/evidence-contract.md>\n" +
    "Neither label tells you which is the original.\n\n" +
    "Find:\n" +
    "1. RECURSIVE_DISCIPLINE_BREACH — any claim or evidence in V or B that " +
    "the skill edited scoring-rubric.md or engineering-baseline.md inline " +
    "(forbidden by C). Quote the literal line.\n" +
    "2. STALE_MISS — dimensions in A whose last_audited >90 days from today " +
    "that B did NOT bump and V did NOT flag.\n" +
    "3. FALSE_STALE — dimensions B re-audited even though A's last_audited " +
    "was within 90 days of today and no --force flag was cited in V.\n" +
    "4. STATE_FORMAT_DRIFT — last_audited: values in B not matching YYYY-MM-DD; " +
    "or labels in V violating E's canonical set " +
    "(Proven result / Engineering guidance / Repo default / Low-evidence area).\n" +
    "5. ADDED — tracking issues cited in V (#NNN) with no corresponding " +
    "search-trail in V (queries tried, sources surfaced). The hard rule " +
    "'always cite the search-trail' must hold.\n" +
    "6. DROPPED — rubric items in A's per-dimension detail tables that " +
    "disappear from B without an underlying contradiction-citation in V.\n" +
    "7. PARTIAL_UPDATE — dimensions where B bumped last_audited but did NOT " +
    "update the Tier-1 source count / grounded-item count even though V " +
    "claims new sources were found.\n\n" +
    "For each item: quote the literal sentence, name file:line, classify with " +
    "one of the seven tokens above. Report under 600 words. Do not rate " +
    "quality. Do not praise the skill's design.\n\n" +
    "A:\n<paste $PRE_MATRIX contents>\n\n" +
    "B:\n<paste $POST_MATRIX contents>\n\n" +
    "V:\n<paste $REPORT contents>\n\n" +
    "C:\n<paste CLAUDE.md Hard Constraints excerpt>\n\n" +
    "E:\n<paste references/evidence-contract.md>"
})
```

Then **dispatch a second time with A and B swapped** (and C/E reordered) — position bias is the dominant LLM-judge artifact in pairwise settings (Shi et al. 2024, arXiv:2406.07791). Take the union of items flagged across both runs.

### Layer C — rubric reconciliation (binary CheckEval-style)

Six yes/no dimensions specialized to this skill. Any `NO` blocks finalization until resolved. CheckEval (arXiv:2403.18771) reports +0.45 inter-evaluator agreement for binary vs. Likert.

```
D1 IDEMPOTENT              Second run of the skill within 90 days of the
                           bumped last_audited produces ZERO mutations to
                           docs/dimension-evidence-coverage.md (modulo
                           whitelisted timestamp fields). External-dependency
                           drift (residual #5) is acknowledged but does not
                           excuse same-day mutation.
                           Layer A STRICT-1 (idempotent_rerun_diff) passes.
                           Ties to F1 IDEMPOTENCY_BREAK, F9 RECURSIVE_DISCIPLINE_BREACH.
                           HIGHEST WEIGHT.

D2 FRESHNESS_RESPECT       Every dimension with last_audited <90 days in PRE
                           is skipped (or report explicitly cites --force);
                           every dimension >=90 days is audited. The 90-day
                           cadence from CLAUDE.md §Development Conventions
                           is honored verbatim.
                           Layer B finds zero STALE_MISS / FALSE_STALE.
                           Ties to F2 STALE_MISS, F3 FALSE_STALE.

D3 SYNC_INTEGRITY          Dimensions where the refresh report claims new
                           Tier-1 sources were found have a matching update
                           to both the Tier-1 source count AND grounded-item
                           count (or coverage score) in the matrix row —
                           never one without the other.
                           Layer B finds zero PARTIAL_UPDATE.
                           Ties to F4 PARTIAL_UPDATE.

D4 SCHEMA_AND_CONTRACT     Every last_audited: value in POST matches the
                           canonical YYYY-MM-DD format. Every evidence label
                           cited in the refresh report appears in
                           references/evidence-contract.md's canonical set.
                           Layer A STRICT-2 (date format) passes; Layer B
                           finds zero STATE_FORMAT_DRIFT.
                           Ties to F5 STATE_FORMAT_DRIFT, F6 EVIDENCE_LABEL_INCONSISTENCY.

D5 VERDICT_HONESTY         Every tracking issue (#NNN) the report claims to
                           have opened is paired with a cited search-trail
                           (queries tried + sources surfaced). No dimension
                           row from the prior matrix silently disappeared.
                           The skill MUST NOT have edited scoring-rubric.md
                           or engineering-baseline.md inline — the report's
                           "Issues opened" section is the only legitimate
                           operationalization channel.
                           Layer A STRICT-3 (frozen_file_breach) passes;
                           Layer B finds zero ADDED / DROPPED / RECURSIVE_DISCIPLINE_BREACH.
                           Ties to F7 EVAL_FALSE_PASS, F9 RECURSIVE_DISCIPLINE_BREACH,
                           F10 NULL_VERDICT_REGRESSION. HIGHEST WEIGHT.

D6 DEPGRAPH_COMPLETENESS   N/A — this skill is not a dependency-graph emitter.
                           Auto-PASS with note.
```

Mapping Layer-A failures → rubric:

- STRICT-1 (idempotent_rerun_diff) fail → D1 NO
- STRICT-2 (date format) fail → D4 NO
- STRICT-3 (frozen file breach) fail → D5 NO (and D1 NO via recursive-discipline reclassification)
- STRICT-4 (dimension set drift) fail → D5 NO

Mapping Layer-B critic tokens → rubric:

- `RECURSIVE_DISCIPLINE_BREACH` → D1 NO + D5 NO
- `STALE_MISS` / `FALSE_STALE` → D2 NO
- `PARTIAL_UPDATE` → D3 NO
- `STATE_FORMAT_DRIFT` → D4 NO
- `ADDED` / `DROPPED` → D5 NO

### Reconciliation outcomes

- **All STRICT pass + Layer B yields zero RECURSIVE_DISCIPLINE_BREACH / STALE_MISS / FALSE_STALE / PARTIAL_UPDATE / STATE_FORMAT_DRIFT / ADDED / DROPPED** → finalize the refresh. Write the report, commit the matrix update, surface follow-up issues.
- **Any STRICT fail OR any blocking critic token** → propose targeted restorations (re-write the bad `last_audited:` value in canonical format, revert any inline mutation of frozen files, restore the dropped dimension row, pair the orphan tracking issue with its search-trail) and re-run Layers A + B on the patched state. **Hard cap: 2 iterations** (per `rules/contract-authoring.md §Small-bound carve-out`; bound = 2 → hard rule, no graceful +1). If still failing after iteration 2, surface to the user; do not auto-publish the refresh.
- **Only SOFT warnings** (`issues_vs_cited_sources` skew, `last_audited_backward_motion`) → finalize but surface the warnings in the refresh-report Summary line so the operator has a final-glance opportunity.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **External-dependency drift.** This skill consults `WebSearch` / `WebFetch` to discover new Tier-1 sources; the same repo state on different days can legitimately yield different mutations because the external corpus moved. D1 is relaxed to "no mutations beyond those traceable to a recorded fetch event in the refresh report"; whether the fetched arXiv index itself is stable is out of scope.
2. **Semantic correctness of "new Tier-1 source".** Layer A and B both treat the Tier-1 filter (peer-reviewed / arXiv / foundation-lab; ≥50 citations OR ≤18 months old) as a self-contained predicate. Neither catches the case where the skill misclassified a blog-post-with-arXiv-shaped-URL as Tier-1. The fix is operator review at the issue-triage step, not the verification layer.
3. **Cross-session state corruption.** The mid-session-freeze rule (CLAUDE.md §Hard Constraints #6) is enforced here against the refresh report's claims and against the POST matrix diff. A skill that edited a frozen file via a sub-shell command and forgot to record it in the report would pass STRICT-3 (no claim) but the breach is still real. Only the Builder agent's session-state guard surfaces this — Layer A is the diff-level downstream confirmation.
4. **Contradiction-citation completeness.** When a Tier-1 source contradicts an existing rubric item, the skill must open a `priority: P1` issue. Layer B can verify the issue is cited; it cannot verify the contradiction itself is real (the cited paper says what the skill claims). NLI on the paper abstract is required and not implemented here.
5. **Refresh-report ↔ tracking-issue body drift.** The report cites `#NNN` opened via `gh`; the actual issue body may have been edited after creation. Layer A and B read the report, not the live GitHub state. Stale issue bodies are invisible to the pipeline.

The refresh report MUST list which residual classes apply to dimensions where the critic surfaced findings flagged `UNCERTAIN`, so the operator has one last human-glance opportunity before the matrix update lands.

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
